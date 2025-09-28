#!/usr/bin/env node
import fs from "fs";
import path from "path";

const [,, specPath, outDir] = process.argv;
if (!specPath || !outDir) {
  console.error("Usage: gen <openapi.yaml> <outdir>");
  process.exit(1);
}

fs.mkdirSync(outDir, { recursive: true });
const spec = fs.readFileSync(specPath, "utf8");

// 简化解析：正则抓路径与方法，生成骨架场景（真实项目可换成 swagger-parser）
const routes = [...spec.matchAll(/^\s{2,}(\/[A-Za-z0-9_\/\-\{\}]+):\s*\n([\s\S]*?)(?=^\s{2,}\/|\Z)/gm)];
let idx = 1;

for (const r of routes) {
  const pathKey = r[1];
  const methods = [...r[2].matchAll(/^\s{4,}(get|post|put|delete|patch):/gmi)].map(m=>m[1].toUpperCase());

  for (const m of methods) {
    const fname = `${String(idx).padStart(2,"0")}_${m}_${pathKey.replace(/[\/\{\}]/g,"_")}.feature`;
    const body = `Feature: ${m} ${pathKey}
  As a client
  I want ${m} ${pathKey}
  So that API contract is honored

  @contract @generated
  Scenario: ${m} ${pathKey} returns 2xx per contract
    Given the API "${pathKey}" exists per OpenAPI
    When I call "${m}" "${pathKey}" with valid payload
    Then the response status should be 200
    And the response should conform to schema "${m} ${pathKey}"

  @contract @error
  Scenario: ${m} ${pathKey} handles errors gracefully
    Given the API "${pathKey}" exists per OpenAPI
    When I call "${m}" "${pathKey}" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
`;
    fs.writeFileSync(path.join(outDir, fname), body);
    console.log(`Generated: ${fname}`);
    idx++;
  }
}

console.log(`\nGenerated ${idx-1} BDD features into ${outDir}`);