pub const DEFAULT_HOST: &str = "127.0.0.1";
pub const DEFAULT_PORT: u16 = 7100;
pub const DEFAULT_MAX_FILES: usize = 12_000;
pub const MAX_FILES_LIMIT: usize = 100_000;
pub const HOTSPOT_LIMIT: usize = 24;
pub const MAX_FILE_READ_BYTES: u64 = 512 * 1024;
pub const MAX_WALK_ENTRIES: usize = 1_000_000;

pub const MANIFEST_FILES: &[&str] = &[
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "build.gradle",
    "pom.xml",
    "composer.json",
    "go.mod",
    "web.xml",
    "cargo.toml",
];

pub const IGNORED_DIRS: &[&str] = &[
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".cache",
    ".gradle",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    "coverage",
    "out",
    "target",
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "fixtures",
];

pub const SUPPORTED_EXTENSIONS: &[&str] = &[
    "py",
    "js",
    "ts",
    "tsx",
    "jsx",
    "java",
    "go",
    "rb",
    "php",
    "cs",
    "kt",
    "rs",
    "mjs",
    "cjs",
    "xml",
    "jsp",
    "jspf",
    "graphql",
    "gql",
];

pub const ROUTE_MARKERS: &[&str] = &[
    "@router.",
    "@app.",
    "app.get(",
    "app.post(",
    "router.get(",
    "router.post(",
    "@getmapping",
    "@postmapping",
    "@requestmapping",
    "handlefunc(",
    "@webservlet",
    "type query",
    "type mutation",
];

pub const AUTH_MARKERS: &[&str] = &[
    "jwt",
    "token",
    "session",
    "auth",
    "bearer",
    "csrf",
    "login",
    "securitycontext",
    "principal",
    "oauth",
];

pub const SOURCE_MARKERS: &[&str] = &[
    "request.",
    "req.body",
    "req.query",
    "req.params",
    "query_params",
    "path_params",
    "$_get",
    "$_post",
    "request.getparameter",
    "variables.",
    "input.",
];

pub const SINK_MARKERS: &[&str] = &[
    "subprocess.",
    "os.system(",
    "child_process.exec",
    "runtime.getruntime().exec",
    "processbuilder",
    "requests.get(",
    "httpx.get(",
    "fetch(",
    "axios.",
    "open(",
    "send_file",
    "fileresponse",
    "pickle.load",
    "yaml.load",
    ".execute(",
    ".query(",
    "$where",
    "eval(",
];
