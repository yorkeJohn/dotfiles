# dotfiles

Personal config, managed with [GNU Stow](https://www.gnu.org/software/stow/). Each folder is a package that mirrors `$HOME`.

- `zsh`: `.zshrc`, Powerlevel10k config, aliases, completions, plugins (submodules)
- `git`: `.gitconfig`, global ignore
- `vscode`: user `settings.json`
- `claude`: Claude Code settings and custom skills (`/cc` fans, `/rgb` lighting)

```sh
git clone --recursive https://github.com/yorkeJohn/dotfiles ~/dotfiles
cd ~/dotfiles && stow zsh git vscode claude
```

Untracked, machine-local: `~/.gitconfig.local` (git identity), `~/.claude/settings.local.json`.
