import re
from pathlib import Path

from app.infrastructure.services.python_flow_analysis import analyze_python_file
from app.infrastructure.services.repository_analysis import INPUT_TOKENS, read_text, relative_path


SOURCE_PATTERNS = {
    "http_input": (
        r"\brequest\.(json|args|form|query_params|headers|cookies|body)\b",
        r"\b(req|request)\.(body|query|params|headers|cookies)\b",
        r"\b(path_params|query_params)\b",
        r"\$_(get|post|request|cookie|files)\b",
        r"@(?:RequestParam|PathVariable|RequestBody)\b",
        r"\brequest\.get(parameter|parametervalues|header|querystring|cookies|requesturi|servletpath|pathinfo)\b",
        r"\bgraphene\.(string|int|boolean|id)\(",
        r"\binfo\.context\b",
        r"\b(args|input|variables)\.[a-z_][a-z0-9_]*\b",
        r"\bcontext\.(req|request|args|user|session)\b",
        r"\bmux\.vars\(",
        r"\br\.(formvalue|url\.query|cookie)\(",
    ),
    "session_input": (
        r"\$_session\b",
        r"\brequest\.session\b",
        r"\bsession\[['\"]",
        r"\bexpress-session\b",
        r"\bhttpsession\b",
        r"\brequest\.getsession\s*\(",
        r"\bsecuritycontext(holder)?\b",
    ),
}

SINK_PATTERNS = {
    "command_execution": (
        r"\bos\.system\(",
        r"\bsubprocess\.(run|popen|call)\(",
        r"\b(exec|execsync|execfile|spawn)\s*\(",
        r"\bchild_process\.(exec|spawn|execfile)\(",
        r"\bruntime\.getruntime\(\)\.exec\b",
        r"\bprocessbuilder\b",
        r"\beval\(",
    ),
    "filesystem_access": (r"\b(open|send_file|FileResponse|write_text|read_text)\(",),
    "outbound_request": (
        r"\brequests\.(get|post|put|delete)\(",
        r"\bhttpx\.(get|post|put|delete)\(",
        r"\bneedle\.(get|post|request)\(",
        r"\b(fetch|axios\.|got\.)",
        r"\bgrpc\.(newclient|dial)\(",
        r"\bresponse\.sendredirect\s*\(",
    ),
    "query_execution": (
        r"\b(cursor\.execute|execute\(|query\()",
        r"\b(mysql_query|mysqli_query|mysqli::query|pdo->query|pdo->exec)\b",
        r"\b(find|findone|findbyid|findandmodify|update|updateone|updatemany|aggregate|insert|remove|findoneandupdate|findoneanddelete)\s*\(",
        r"\b\$where\b",
        r"\b\$(regex|ne|or|and)\b",
        r"\bexecutequery\s*\(",
        r"\bexecuteupdate\s*\(",
        r"\bstatement\.execute\s*\(",
        r"\bpreparedstatement\.execute(?:query|update)?\s*\(",
        r"\btext\s*\(",
        r"\bprisma\.\$queryraw\b",
        r"\bsequelize\.query\b",
        r"\bknex\.raw\b",
    ),
    "unsafe_deserialization": (
        r"\bpickle\.(load|loads)\(",
        r"\byaml\.load\(",
        r"\bobjectinputstream\b",
        r"\breadobject\s*\(",
        r"\bspelparserconfiguration\b",
        r"\bspel\b",
        r"\bexpressionfactory\b",
        r"\bscriptenginemanager\b",
        r"\bdecode\(token,\s*options\s*=\s*\{[^\}]*verify_signature[\"']?\s*:\s*false",
    ),
}

SANITIZER_PATTERNS = {
    "path_normalization": (r"\b(resolve|realpath|normpath|relative_to|safe_join)\(",),
    "input_validation": (
        r"\b(validate|sanitize|escape|allowlist|whitelist|filter_var|htmlspecialchars|intval|preparedstatement)\(",
        r"\b(ipaddress|urlparse|urlsplit|graphql-shield|depthlimit|costanalysis)\b",
    ),
    "sql_parameterization": (r"\bpreparedstatement\b", r"\bsetparameter\b", r"\$eq\b"),
}


def build_source_sink_registry(source_root: Path, files: list[Path], framework_profile: dict) -> dict:
    sources: list[dict] = []
    sinks: list[dict] = []
    sanitizers: list[dict] = []
    python_analyses: dict[str, dict] = {}

    for path in files:
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".php", ".java", ".go", ".jsp", ".jspf"}:
            continue
        file_path = relative_path(path, source_root)
        text = read_text(path)
        lowered = text.lower()

        if path.suffix.lower() == ".py":
            analysis = analyze_python_file(path, source_root)
            python_analyses[file_path] = analysis
            sources.extend(analysis["sources"])
            sinks.extend(analysis["sinks"])
            sanitizers.extend(analysis["sanitizers"])

        if framework_profile["primary_framework"] == "fastapi" and ("from fastapi import" in lowered or "@app." in lowered or "@router." in lowered):
            if any(token in lowered for token in INPUT_TOKENS):
                source_line = _first_match_line(text, SOURCE_PATTERNS["http_input"])
                if source_line is not None:
                    sources.append({"file": file_path, "line": source_line, "kind": "http_input", "label": "FastAPI request data"})

        if path.suffix.lower() == ".php":
            sources.extend(_build_php_sources(text, file_path))
            sinks.extend(_build_php_sinks(text, file_path))
            sanitizers.extend(_build_php_sanitizers(text, file_path))

        if path.suffix.lower() in {".java", ".jsp", ".jspf", ".xml"}:
            sources.extend(_build_spring_sources(text, file_path))
            sources.extend(_build_servlet_sources(text, file_path))
            sinks.extend(_build_spring_sinks(text, file_path))
            sinks.extend(_build_servlet_sinks(text, file_path))
            sanitizers.extend(_build_spring_sanitizers(text, file_path))
            sanitizers.extend(_build_servlet_sanitizers(text, file_path))

        if path.suffix.lower() in {".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}:
            sinks.extend(_build_node_sinks(text, file_path))
            sources.extend(_build_node_sources(text, file_path))
            sanitizers.extend(_build_node_sanitizers(text, file_path))
            if any(token in lowered for token in ("graphql", "apollo", "resolver", "type query", "type mutation")):
                sources.extend(_build_graphql_script_sources(text, file_path))
                sinks.extend(_build_graphql_script_sinks(text, file_path))
                sanitizers.extend(_build_graphql_script_sanitizers(text, file_path))

        if path.suffix.lower() == ".go":
            sinks.extend(_build_go_sinks(text, file_path))
            sources.extend(_build_go_sources(text, file_path))
            sanitizers.extend(_build_go_sanitizers(text, file_path))

        if path.suffix.lower() in {".py", ".graphql", ".gql"} and any(
            token in lowered for token in ("graphene", "graphql", "/graphql", "flask_graphql_auth", "type query", "type mutation")
        ):
            sources.extend(_build_graphql_sources(text, file_path))
            sinks.extend(_build_graphql_sinks(text, file_path))
            sanitizers.extend(_build_graphql_sanitizers(text, file_path))

        sources.extend(_match_registry(text, file_path, SOURCE_PATTERNS, "source"))
        sinks.extend(_match_registry(text, file_path, SINK_PATTERNS, "sink"))
        sanitizers.extend(_match_registry(text, file_path, SANITIZER_PATTERNS, "sanitizer"))

    return {
        "sources": _dedupe_registry_items(sources)[:2000],
        "sinks": _dedupe_registry_items(sinks)[:2000],
        "sanitizers": _dedupe_registry_items(sanitizers)[:2000],
        "python_analyses": python_analyses,
        "summary": {
            "source_count": len(_dedupe_registry_items(sources)),
            "sink_count": len(_dedupe_registry_items(sinks)),
            "sanitizer_count": len(_dedupe_registry_items(sanitizers)),
        },
    }


def _match_registry(text: str, file_path: str, patterns: dict[str, tuple[str, ...]], kind: str) -> list[dict]:
    items: list[dict] = []
    for label, entries in patterns.items():
        line = _first_match_line(text, entries)
        if line is None:
            continue
        items.append({"file": file_path, "line": line, "kind": label, "label": label.replace("_", " "), "type": kind})
    return items


def _first_match_line(text: str, patterns: tuple[str, ...]) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if any(re.search(pattern, lowered) for pattern in patterns):
            return index
    return None


def _dedupe_registry_items(items: list[dict]) -> list[dict]:
    deduped: dict[tuple[str, int, str], dict] = {}
    for item in items:
        deduped[(item["file"], int(item["line"]), item["kind"])] = item
    return list(deduped.values())


def _build_php_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (
                r"\$_get\b",
                r"\$_post\b",
                r"\$_request\b",
                r"\$_cookie\b",
                r"\$_files\b",
            ),
            "session_input": (r"\$_session\b",),
        },
        "source",
    )


def _build_php_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "query_execution": (r"\b(mysql_query|mysqli_query|mysqli::query|pdo->query|pdo->exec)\b",),
            "command_execution": (r"\b(exec|system|shell_exec|passthru)\s*\(",),
            "filesystem_access": (r"\b(include|require|include_once|require_once|fopen|file_get_contents)\s*\(",),
            "unsafe_deserialization": (r"\bunserialize\s*\(",),
        },
        "sink",
    )


def _build_php_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (r"\b(filter_var|htmlspecialchars|intval|preg_match|mysqli_real_escape_string)\s*\(",),
            "sql_parameterization": (r"\bprepare\s*\(", r"\bbind_param\s*\("),
        },
        "sanitizer",
    )


def _build_spring_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (
                r"@requestparam\b",
                r"@pathvariable\b",
                r"@requestbody\b",
                r"@modelattribute\b",
                r"@requestheader\b",
                r"@cookievalue\b",
                r"httprequest\b",
                r"authenticationprincipal\b",
                r"\bprincipal\b",
                r"@requestmapping\b",
                r"@(get|post|put|delete|patch)mapping\b",
            ),
            "session_input": (r"httpsession\b", r"securitycontext\b", r"\bauthentication\b", r"\bsecuritycontextholder\b"),
        },
        "source",
    )


def _build_spring_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "command_execution": (r"\bruntime\.getruntime\(\)\.exec\b", r"\bprocessbuilder\b"),
            "unsafe_deserialization": (
                r"\breadobject\s*\(",
                r"\bobjectinputstream\b",
                r"\bspel\b",
                r"\bspelparserconfiguration\b",
                r"\bexpressionfactory\b",
                r"\bscriptenginemanager\b",
            ),
            "query_execution": (r"\bjdbctemplate\.", r"\bentitymanager\.createquery\b", r"\bcreateNativeQuery\b"),
            "filesystem_access": (r"\btemplateengine\.process\b", r"\bthymeleaf\b", r"\bmodelandview\b"),
        },
        "sink",
    )


def _build_spring_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (r"@valid\b", r"bindingresult\b", r"\bvalidator\b"),
            "sql_parameterization": (r"\bpreparedstatement\b", r"\bsetparameter\b"),
        },
        "sanitizer",
    )


def _build_servlet_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (
                r"\brequest\.getparameter\s*\(",
                r"\brequest\.getheader\s*\(",
                r"\brequest\.getquerystring\s*\(",
                r"\brequest\.getcookies\s*\(",
                r"\brequest\.getservletpath\s*\(",
                r"\brequest\.getpathinfo\s*\(",
                r"\brequest\.getrequesturi\s*\(",
                r"@pathparam\b",
                r"@queryparam\b",
                r"@formparam\b",
            ),
            "session_input": (r"\brequest\.getsession\s*\(", r"\bhttpsession\b", r"\brequest\.isuserinrole\s*\(", r"\bprincipal\b"),
        },
        "source",
    )


def _build_servlet_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "query_execution": (
                r"\bstatement\.executequery\s*\(",
                r"\bstatement\.executeupdate\s*\(",
                r"\bstatement\.execute\s*\(",
                r"\bpreparedstatement\.execute(?:query|update)?\s*\(",
                r"\bgetconnection\s*\(",
            ),
            "outbound_request": (r"\bresponse\.sendredirect\s*\(", r"\burlconnection\b", r"\bhttpclient\b"),
            "filesystem_access": (r"\brequest\.getrequestdispatcher\s*\(", r"\bdispatcher\.(forward|include)\s*\(", r"<jsp:(include|forward)\b"),
            "command_execution": (r"\bruntime\.getruntime\(\)\.exec\b", r"\bprocessbuilder\b"),
            "unsafe_deserialization": (r"\bexpressionfactory\b", r"\bscriptenginemanager\b"),
        },
        "sink",
    )


def _build_servlet_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (r"\binteger\.parseint\s*\(", r"\blong\.parselong\s*\(", r"\burlencoder\.encode\s*\("),
            "sql_parameterization": (r"\bpreparedstatement\b", r"\bpreparestatement\s*\(", r"\bsetstring\s*\("),
        },
        "sanitizer",
    )


def _build_node_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (r"\b(req|request)\.(body|query|params|headers|cookies)\b", r"\b(req|request)\.param\s*\("),
            "session_input": (r"\b(req|request)\.session\b", r"\b(req|request)\.user\b"),
        },
        "source",
    )


def _build_node_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "query_execution": (
                r"\b(find|findone|findbyid|findandmodify|update|updateone|updatemany|aggregate|insert|remove)\s*\(",
                r"\b\$where\b",
                r"\bmongoose\.",
                r"\bdb\.collection\s*\(",
            ),
            "command_execution": (r"\b(exec|spawn|execfile)\s*\(", r"\bchild_process\.(exec|spawn|execfile)\("),
            "outbound_request": (r"\bneedle\.(get|post|request)\(", r"\bres\.redirect\s*\(", r"\baxios\.", r"\bfetch\s*\(", r"\bgot\."),
            "auth_state_change": (r"\b(req|request)\.session\.[a-zA-Z_][a-zA-Z0-9_]*\s*=",),
        },
        "sink",
    )


def _build_node_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (
                r"\bvalidator\.",
                r"\bjoi\.",
                r"\bzod\.",
                r"\bexpress-validator\b",
                r"\bmongo-sanitize\b",
                r"\besapi\.encoder\(",
            ),
            "sql_parameterization": (r"\bvalidator\.escape\(", r"\bescape\("),
        },
        "sanitizer",
    )


def _build_graphql_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (
                r"\bgraphene\.(string|int|boolean|id)\(",
                r"\binfo\.context\.json\b",
                r"\brequest\.(remote_addr|headers|get_json|json)\b",
                r"\btype\s+(query|mutation)\b",
            ),
            "session_input": (r"\btoken\s*=\s*graphene\.string\(", r"\bcreate_access_token\b"),
        },
        "source",
    )


def _build_graphql_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "command_execution": (r"\bhelpers\.run_cmd\s*\(", r"\bos\.popen\s*\("),
            "query_execution": (r"\btext\s*\(", r"\bquery\.filter\(.+like\(",),
            "filesystem_access": (r"\bsave_file\s*\(", r"\bopen\s*\(", r"\bweb_uploaddir\s*\+"),
            "outbound_request": (r"\bcurl\s+--insecure\b", r"\bimportpaste\b"),
            "unsafe_deserialization": (r"\bdecode\(token,\s*options\s*=\s*\{[^\}]*verify_signature[\"']?\s*:\s*false",),
        },
        "sink",
    )


def _build_graphql_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (
                r"\bstrip_dangerous_characters\s*\(",
                r"\bon_denylist\s*\(",
                r"\boperation_name_allowed\s*\(",
                r"\bdepth_exceeded\s*\(",
                r"\bcost_exceeded\s*\(",
            ),
        },
        "sanitizer",
    )


def _build_graphql_script_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (
                r"\b(args|input|variables)\.[a-z_][a-z0-9_]*\b",
                r"\bcontext\.(req|request|args)\b",
                r"\bgraphqlresolveinfo\b",
                r"\bapollo(server)?\b",
            ),
            "session_input": (r"\bcontext\.(user|session)\b", r"\b(req|request)\.user\b"),
        },
        "source",
    )


def _build_graphql_script_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "query_execution": (
                r"\b(prisma\.\$queryraw|sequelize\.query|knex\.raw)\b",
                r"\b(find|findone|aggregate|updateone|collection)\s*\(",
                r"\b\$where\b",
            ),
            "command_execution": (r"\b(exec|spawn|execfile)\s*\(", r"\bchild_process\.(exec|spawn|execfile)\("),
            "outbound_request": (r"\baxios\.", r"\bfetch\s*\(", r"\bgot\."),
        },
        "sink",
    )


def _build_graphql_script_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (
                r"\bgraphql-shield\b",
                r"\bshield\s*\(",
                r"\bdepthlimit\s*\(",
                r"\bcostanalysis\s*\(",
                r"\ballowlist\b",
            ),
        },
        "sanitizer",
    )


def _build_go_sources(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "http_input": (
                r"\bhandlefunc\(",
                r"\bmux\.vars\s*\(",
                r"\br\.(formvalue|url\.query|cookie)\s*\(",
                r"\bhttp\.request\b",
            ),
        },
        "source",
    )


def _build_go_sinks(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "outbound_request": (
                r"\bgrpc\.newclient\s*\(",
                r"\bgrpc\.dial\s*\(",
                r"\bhttp\.(get|post|newrequest)\s*\(",
                r"\bos\.getenv\(\s*\"[A-Z0-9_]*_SERVICE_ADDR\"",
                r"\bos\.getenv\(\s*\"[A-Z0-9_]*_SERVICE_URL\"",
            ),
        },
        "sink",
    )


def _build_go_sanitizers(text: str, file_path: str) -> list[dict]:
    return _match_registry(
        text,
        file_path,
        {
            "input_validation": (r"\bwhitelistedcurrencies\b", r"\bmustmapenv\s*\("),
        },
        "sanitizer",
    )
