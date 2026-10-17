const https = require("https");
const http = require("http");
const { URL } = require("url");

module.exports.config = {
  api: { bodyParser: false },
};

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

module.exports = async function handler(req, res) {
  const gateway = process.env.GATEWAY_URL;
  if (!gateway) {
    res.status(503).json({ ok: false, error: "GATEWAY_URL is not set" });
    return;
  }
  const path = [].concat(req.query.path || []).join("/");
  const target = new URL(path, gateway.endsWith("/") ? gateway : gateway + "/");
  const body = req.method === "GET" || req.method === "HEAD" ? null : await readBody(req);
  const headers = { accept: "application/json, */*", "user-agent": "linelock-console" };
  if (req.headers["content-type"]) headers["content-type"] = req.headers["content-type"];
  if (body) headers["content-length"] = String(body.length);

  const lib = target.protocol === "https:" ? https : http;
  let upstream;
  try {
    upstream = await new Promise((resolve, reject) => {
      const request = lib.request(
        target,
        { method: req.method, headers, timeout: 55000 },
        (response) => {
          const chunks = [];
          response.on("data", (chunk) => chunks.push(chunk));
          response.on("end", () => resolve({ status: response.statusCode || 502, headers: response.headers, body: Buffer.concat(chunks) }));
        }
      );
      request.on("error", reject);
      request.on("timeout", () => request.destroy(new Error("gateway timeout")));
      if (body) request.write(body);
      request.end();
    });
  } catch (error) {
    res.status(502).json({ ok: false, error: String(error && error.message ? error.message : error) });
    return;
  }

  res.status(upstream.status);
  const type = upstream.headers["content-type"];
  if (type) res.setHeader("content-type", type);
  res.send(upstream.body);
};
