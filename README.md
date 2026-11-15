# dotfiles

Personal config, managed with [GNU Stow](https://www.gnu.org/software/stow/). Each folder is a package that mirrors `$HOME`.

- `zsh`: `.zshrc`, Powerlevel10k config, aliases, completions, plugins (submodules)
- `git`: `.gitconfig`, global ignore
- `nvim`: minimal `init.lua`, Monokai (submodule) with a transparent background
- `vscode`: user `settings.json`
- `claude`: Claude Code settings and custom skills (`/cooling` fans, `/lighting` RGB)

```sh
git clone --recursive https://github.com/yorkeJohn/dotfiles ~/dotfiles
cd ~/dotfiles && stow */
```

`stow -R */` re-links after adding or removing files; `stow -D */` removes the links.

Untracked, machine-local: `~/.gitconfig.local` (git identity), `~/.claude/settings.local.json`.
