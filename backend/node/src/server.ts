import { config } from "./config.js";
import { logStartup } from "./logger.js";
import { createNodeIoServer } from "./server/createNodeIoServer.js";

const server = createNodeIoServer(config);

server.listen(config.port, config.host, () => {
  logStartup(`listening on http://${config.host}:${config.port}`);
  logStartup("running as standalone local I/O service; Python API is not proxied");
});

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

function shutdown(): void {
  server.close(() => {
    process.exit(0);
  });
}
