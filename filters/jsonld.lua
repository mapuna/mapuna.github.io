-- Inject a <link rel="canonical">, <meta property="og:url">, and a JSON-LD
-- BlogPosting/WebSite block into <head>, built from document metadata.
-- Quarto does not emit canonical links or structured data on its own.

local SITE_URL = "https://mapuna.github.io"

local function stringify(m)
  if m == nil then return nil end
  local s = pandoc.utils.stringify(m)
  if s == "" then return nil end
  return s
end

local function json_escape(s)
  return (s:gsub('[%z\1-\31\\"<>]', function(c)
    local map = { ['"'] = '\\"', ['\\'] = '\\\\', ['\n'] = '\\n',
                  ['\r'] = '\\r', ['\t'] = '\\t', ['<'] = '\\u003c',
                  ['>'] = '\\u003e' }
    return map[c] or string.format('\\u%04x', string.byte(c))
  end))
end

local function input_file()
  if quarto and quarto.doc and quarto.doc.input_file then
    return quarto.doc.input_file
  elseif PANDOC_STATE and PANDOC_STATE.input_files then
    return PANDOC_STATE.input_files[1]
  end
  return nil
end

-- The ISO date from the source .qmd front matter. Quarto localizes meta.date
-- ("May 4, 2026") before user filters run and keeps no ISO copy, but
-- schema.org datePublished must be ISO 8601.
local function frontmatter_iso_date()
  local f = input_file()
  if not f then return nil end
  local fh = io.open(f, "r")
  if not fh then return nil end
  local content = fh:read("*a")
  fh:close()
  local fm = content:match("^%-%-%-%s*\n(.-)\n%-%-%-")
  if not fm then return nil end
  return fm:match("[\n^]date:%s*['\"]?(%d%d%d%d%-%d%d%-%d%d)")
end

-- source .qmd path (project-relative) -> site path ("/", "/about.html",
-- "/posts/<slug>/")
local function site_path()
  local f = input_file()
  if not f then return "/" end
  f = f:gsub("\\", "/"):gsub("^%./", "")
  local pd = os.getenv("QUARTO_PROJECT_DIR") or os.getenv("QUARTO_PROJECT_ROOT")
  if pd then
    pd = pd:gsub("\\", "/")
    if f:sub(1, #pd + 1) == pd .. "/" then f = f:sub(#pd + 2) end
  end
  if f == "index.qmd" then return "/" end
  local slug = f:match("^(.+)/index%.qmd$")
  if slug then return "/" .. slug .. "/" end
  local base = f:match("^(.+)%.qmd$")
  if base then return "/" .. base .. ".html" end
  return "/"
end

function Meta(meta)
  local title = stringify(meta.title)
  local desc = stringify(meta.description)
  local date = frontmatter_iso_date()
  local author = stringify(meta.author) or "Anupam Gupta"
  local url = SITE_URL .. site_path()

  local typ = date and "BlogPosting" or "WebSite"
  local parts = {
    '"@context":"https://schema.org"',
    '"@type":"' .. typ .. '"',
    '"headline":"' .. json_escape(title or "Bits and Priors") .. '"',
    '"url":"' .. json_escape(url) .. '"',
  }
  if desc then parts[#parts + 1] = '"description":"' .. json_escape(desc) .. '"' end
  if date then parts[#parts + 1] = '"datePublished":"' .. json_escape(date) .. '"' end
  parts[#parts + 1] =
    '"author":{"@type":"Person","name":"' .. json_escape(author) .. '"}'
  parts[#parts + 1] = '"publisher":{"@type":"Person","name":"Anupam Gupta"}'

  local jsonld = '<script type="application/ld+json">{'
    .. table.concat(parts, ",") .. '}</script>'
  local canonical = string.format('<link rel="canonical" href="%s">', url)
  local ogurl = string.format('<meta property="og:url" content="%s">', url)

  -- add_html_dependency's `head` is injected into <head>; include_text
  -- ("in-header", ...) lands in <body> in this Quarto version, where a
  -- rel=canonical would be ignored by crawlers. Name is per-page so Quarto
  -- does not dedup one page's block onto another.
  local page_id = url:gsub("%W", "_")
  quarto.doc.add_html_dependency({
    name = "seo-meta-" .. page_id,
    version = "1.0.0",
    head = canonical .. "\n" .. ogurl .. "\n" .. jsonld,
  })
  return meta
end
