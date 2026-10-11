const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const ts = require("typescript");
const source = fs.readFileSync(
  path.resolve(__dirname, "../src/ui/format.ts"),
  "utf8",
);
const output = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const context = { exports: {} };
vm.runInNewContext(output, context);
const { formatMoney, maskAccount } = context.exports;
assert.equal(formatMoney(80000), "₹800.00");
assert.equal(formatMoney(987654321), "₹98,76,543.21");
assert.equal(formatMoney(1), "₹0.01");
assert.equal(formatMoney(-1), "−₹0.01");
assert.equal(formatMoney(0), "₹0.00");
assert.equal(formatMoney(Number.MAX_SAFE_INTEGER), "₹9,00,71,99,25,47,409.91");
assert.equal(formatMoney(Number.MAX_SAFE_INTEGER + 1), "Amount unavailable");
assert.equal(formatMoney(1.5), "Amount unavailable");
assert.equal(maskAccount("**** 4821"), "•••• 4821");
assert.equal(maskAccount("•••• king"), "•••• king");
console.log("10 integer money/masking checks passed.");
