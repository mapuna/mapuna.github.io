-- Append a prev/next <nav> to each blog post, using the ordered table in
-- _manifest.lua (written by scripts/build_manifest.py as a pre-render step).
-- Previous = older post, Next = newer post. No runtime JS.

local function html_escape(s)
  return (s:gsub("[&<>\"]", {
    ["&"] = "&amp;", ["<"] = "&lt;", [">"] = "&gt;", ["\""] = "&quot;",
  }))
end

local function project_dir()
  return os.getenv("QUARTO_PROJECT_DIR") or os.getenv("QUARTO_PROJECT_ROOT")
end

local function load_manifest()
  local candidates = {}
  local pd = project_dir()
  if pd then candidates[#candidates + 1] = pd .. "/_manifest.lua" end
  candidates[#candidates + 1] = "_manifest.lua"
  for _, path in ipairs(candidates) do
    local ok, m = pcall(dofile, path)
    if ok and type(m) == "table" then return m end
  end
  return nil
end

-- Absolute source path of the .qmd being rendered, normalized to a
-- project-relative POSIX path like "posts/<slug>/index.qmd".
local function input_path()
  local f
  if quarto and quarto.doc and quarto.doc.input_file then
    f = quarto.doc.input_file
  elseif PANDOC_STATE and PANDOC_STATE.input_files then
    f = PANDOC_STATE.input_files[1]
  end
  if not f then return nil end

  f = f:gsub("\\", "/"):gsub("^%./", "")
  local pd = project_dir()
  if pd then
    pd = pd:gsub("\\", "/")
    if f:sub(1, #pd + 1) == pd .. "/" then
      f = f:sub(#pd + 2)
    end
  end
  return f
end

local function find_index(manifest, input)
  for i, entry in ipairs(manifest) do
    if entry.path == input then return i end
  end
  -- fall back to a suffix match if the path could not be made project-relative
  for i, entry in ipairs(manifest) do
    if #input >= #entry.path and input:sub(-#entry.path) == entry.path then
      return i
    end
  end
  return nil
end

local function cell(entry, label, side)
  return string.format(
    '<div class="post-nav__%s"><span class="post-nav__label">%s</span>'
      .. '<a href="%s">%s</a></div>',
    side, label, entry.href, html_escape(entry.title))
end

function Pandoc(doc)
  local input = input_path()
  if not input or not input:match("^posts/[^/]+/index%.qmd$") then
    return doc
  end

  local manifest = load_manifest()
  if not manifest then return doc end

  local idx = find_index(manifest, input)
  if not idx then return doc end

  local prev, nxt = manifest[idx - 1], manifest[idx + 1]
  if not prev and not nxt then return doc end

  local parts = { '<nav class="post-nav">' }
  if prev then parts[#parts + 1] = cell(prev, "\u{2190} Previous", "prev") end
  if nxt then parts[#parts + 1] = cell(nxt, "Next \u{2192}", "next") end
  parts[#parts + 1] = "</nav>"

  table.insert(doc.blocks, pandoc.RawBlock("html", table.concat(parts)))
  return doc
end
