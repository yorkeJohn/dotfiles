-- Plugins live in pack/plugins/start/ as git submodules and load automatically.

-- Leader must be set before any mappings that use it.
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- nvim-tree replaces netrw; disable netrw before anything loads it.
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

-- Options ---------------------------------------------------------------------
local opt = vim.opt
opt.number = true             -- line numbers
opt.expandtab = true          -- 2-space indent, matching VS Code
opt.tabstop = 2
opt.shiftwidth = 2
opt.softtabstop = 2
opt.clipboard = "unnamedplus" -- yank/paste via the system clipboard (uses xclip)
opt.ignorecase = true         -- case-insensitive search...
opt.smartcase = true          -- ...unless the pattern has a capital
opt.undofile = true           -- keep undo history after closing a file
opt.mouse = "a"

-- Colours ---------------------------------------------------------------------
-- Clear backgrounds so the terminal's own background shows through.
-- Runs on every ColorScheme event, so it also survives switching schemes.
vim.api.nvim_create_autocmd("ColorScheme", {
  callback = function()
    for _, group in ipairs({
      "Normal", "NormalNC", "NormalFloat", "FloatBorder",
      "SignColumn", "LineNr", "CursorLineNr", "FoldColumn",
      "EndOfBuffer", "StatusLine", "StatusLineNC", "TabLineFill",
      "NvimTreeNormal", "NvimTreeNormalNC", "NvimTreeEndOfBuffer",
    }) do
      vim.api.nvim_set_hl(0, group, vim.tbl_extend("force",
        vim.api.nvim_get_hl(0, { name = group, link = false }), { bg = "NONE", ctermbg = "NONE" }))
    end
  end,
})

vim.cmd.colorscheme("monokai")

-- Treesitter ------------------------------------------------------------------
-- Uses the frozen `master` branch, the last one supporting Neovim 0.11.
-- Parsers compile with gcc into the data dir, keeping the submodule clean.
local parser_dir = vim.fn.stdpath("data") .. "/treesitter"
opt.runtimepath:prepend(parser_dir)

require("nvim-treesitter.configs").setup({
  parser_install_dir = parser_dir,
  ensure_installed = {
    "bash", "css", "html", "javascript", "json", "lua", "markdown",
    "markdown_inline", "python", "query", "rust", "toml", "tsx",
    "typescript", "vim", "vimdoc", "yaml",
  },
  auto_install = true, -- install a missing parser when opening a new file type
  highlight = { enable = true },
  indent = { enable = true },
})

-- File explorer ---------------------------------------------------------------
require("nvim-tree").setup({
  view = { width = 32 },
  filters = { dotfiles = false },
})

vim.keymap.set("n", "<leader>e", "<cmd>NvimTreeToggle<CR>", { desc = "Toggle file tree" })
vim.keymap.set("n", "<leader>f", "<cmd>NvimTreeFindFile<CR>", { desc = "Reveal current file in tree" })
