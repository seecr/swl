-- Pandoc filter for the reference PDF (Typst).

-- Keeps an example on one page: a code block can't be split over two pages, and the
-- paragraph right before it (usually "... like this:") stays on the same page as the code.
local function wrap(blocks)
  local out = pandoc.Blocks{}
  local i = 1
  while i <= #blocks do
    local b, nxt = blocks[i], blocks[i + 1]
    if (b.t == "Para" or b.t == "Plain") and nxt and nxt.t == "CodeBlock" then
      out:insert(pandoc.RawBlock("typst", "#block(breakable: false)["))
      out:insert(b)
      out:insert(nxt)
      out:insert(pandoc.RawBlock("typst", "]"))
      i = i + 2
    elseif b.t == "CodeBlock" then
      out:insert(pandoc.RawBlock("typst", "#block(breakable: false)["))
      out:insert(b)
      out:insert(pandoc.RawBlock("typst", "]"))
      i = i + 1
    else
      out:insert(b)
      i = i + 1
    end
  end
  return out
end

-- Every list of blocks: the document, but also list items, block quotes and so on.
function Blocks(blocks)
  return wrap(blocks)
end

-- A table with a header row gets header-row() from the template around it: bold and grey.
-- Tables without one (an empty header row in markdown) start with plain content.
function Table(t)
  if #t.head.rows > 0 then
    return {
      pandoc.RawBlock("typst", "#header-row["),
      t,
      pandoc.RawBlock("typst", "]"),
    }
  end
end
