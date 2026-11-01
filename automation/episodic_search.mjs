#!/usr/bin/env node
// Usage: node episodic_search.mjs <pluginRoot> <query> <currentSessionId>
// The parent hook owns its timeout and treats these records as untrusted history.
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { format } from 'node:util';

const MAX_OUTPUT_CHARS = 3000;
const MAX_SNIPPET_CHARS = 700;
const MAX_RESULTS = 3;

// The library can print migration diagnostics. Reserve stdout for one JSON object.
console.log = (...args) => process.stderr.write(`${format(...args)}\n`);

function compactText(value, limit) {
  if (typeof value !== 'string') return '';
  return value.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '')
    .replace(/\s+/g, ' ').trim().slice(0, limit);
}

function isCurrentConversation(exchange, currentSessionId) {
  if (exchange.sessionId === currentSessionId) return true;
  // Older indexed rows may lack sessionId; sidechain files can live under it.
  const segments = exchange.archivePath.replaceAll('\\', '/').split('/');
  return segments.some(segment => segment === currentSessionId ||
    segment === `${currentSessionId}.jsonl`);
}

function boundedResults(rawResults, currentSessionId) {
  const results = [];
  const seenPaths = new Set();
  const seenSessions = new Set();

  for (const raw of rawResults) {
    if (results.length >= MAX_RESULTS) break;
    const exchange = raw?.exchange;
    if (!exchange || typeof exchange.archivePath !== 'string' ||
        !path.isAbsolute(exchange.archivePath) || typeof exchange.id !== 'string') continue;
    if (exchange.harness && exchange.harness !== 'claude') continue;
    if (isCurrentConversation(exchange, currentSessionId)) continue;
    if (seenPaths.has(exchange.archivePath) ||
        (exchange.sessionId && seenSessions.has(exchange.sessionId))) continue;

    const user = compactText(exchange.userMessage, 200);
    const assistant = compactText(exchange.assistantMessage, 475);
    const result = {
      id: exchange.id,
      source: 'episodic-memory',
      path: exchange.archivePath,
      sessionId: typeof exchange.sessionId === 'string' ? exchange.sessionId : null,
      project: compactText(exchange.project, 120),
      date: compactText(exchange.timestamp, 40),
      lineStart: Number.isInteger(exchange.lineStart) ? exchange.lineStart : null,
      lineEnd: Number.isInteger(exchange.lineEnd) ? exchange.lineEnd : null,
      similarity: Number.isFinite(raw.similarity) ? raw.similarity : null,
      snippet: compactText(`User: ${user} Assistant: ${assistant}`, MAX_SNIPPET_CHARS),
    };

    // Bound the serialized JSON, including escaping and all source metadata.
    while (result.snippet.length > 0 &&
           JSON.stringify({ results: [...results, result] }).length > MAX_OUTPUT_CHARS) {
      const overflow = JSON.stringify({ results: [...results, result] }).length - MAX_OUTPUT_CHARS;
      result.snippet = result.snippet.slice(0, Math.max(0, result.snippet.length - overflow - 1));
    }
    if (!result.snippet ||
        JSON.stringify({ results: [...results, result] }).length > MAX_OUTPUT_CHARS) continue;

    results.push(result);
    seenPaths.add(exchange.archivePath);
    if (exchange.sessionId) seenSessions.add(exchange.sessionId);
  }
  return results;
}

async function main() {
  const [pluginRoot, rawQuery, rawSessionId] = process.argv.slice(2);
  const query = typeof rawQuery === 'string' ? rawQuery.trim().slice(0, 2000) : '';
  const currentSessionId = typeof rawSessionId === 'string' ? rawSessionId.trim() : '';
  if (!query || !currentSessionId) return { results: [] };
  if (!pluginRoot || !path.isAbsolute(pluginRoot)) return { results: [], error: 'invalid_plugin_root' };

  try {
    const moduleUrl = pathToFileURL(path.join(pluginRoot, 'dist', 'search.js')).href;
    const { searchConversations } = await import(moduleUrl);
    const rawResults = await searchConversations(query, {
      mode: 'both', limit: MAX_RESULTS, include_sidechains: false,
    });
    if (!Array.isArray(rawResults)) return { results: [], error: 'invalid_search_response' };
    return { results: boundedResults(rawResults, currentSessionId) };
  } catch {
    // Do not echo a query, transcript, SQL statement, or stack trace on failure.
    return { results: [], error: 'search_failed' };
  }
}

process.stdout.write(`${JSON.stringify(await main())}\n`);
