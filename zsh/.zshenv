# Read by every zsh (interactive or not), so keep this to environment only.
typeset -U path PATH

[[ -f "$HOME/.cargo/env" ]] && . "$HOME/.cargo/env"

export BUN_INSTALL="$HOME/.bun"
path=("$HOME/.local/bin" "$BUN_INSTALL/bin" $path)
