-- Plugins live in pack/plugins/start/ as git submodules and load automatically.

-- Clear backgrounds so the terminal's own background shows through.
-- Runs on every ColorScheme event, so it also survives switching schemes.
vim.api.nvim_create_autocmd("ColorScheme", {
  callback = function()
    for _, group in ipairs({
      "Normal", "NormalNC", "NormalFloat", "FloatBorder",
      "SignColumn", "LineNr", "CursorLineNr", "FoldColumn",
      "EndOfBuffer", "StatusLine", "StatusLineNC", "TabLineFill",
    }) do
      vim.api.nvim_set_hl(0, group, vim.tbl_extend("force",
        vim.api.nvim_get_hl(0, { name = group, link = false }), { bg = "NONE", ctermbg = "NONE" }))
    end
  end,
})

vim.cmd.colorscheme("monokai")
