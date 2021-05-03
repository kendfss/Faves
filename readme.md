# Faves
This is an implementation/elaboration on Helder Sepulveda's [Notepad++ plugin]((https:/github.com/heldersepu). Using this plugin you will be able to maintain a list of shortcuts to files and folders of your choice.  
This plugin is implemented as an input-friendly TextCommand, so you can set keybindings in your file by using the following syntax:
```json
{ "keys": ["ctrl+shift+0"], "command": "favourites", "args": { "text": "0", } },
{ "keys": ["ctrl+shift+1"], "command": "favourites", "args": { "text": "1", } },
{ "keys": ["ctrl+shift+2"], "command": "favourites", "args": { "text": "2", } },
/ etc
```
Using this exact syntax will grant you access to 10 shortcuts, but there's also the option to use the Command Palette which grants arbitrarily many shortcuts, each separated by a comma, a space, or both (in either order).

### Why
###### Sublime already offers comprehensive keybinding commands and arguments. Why bother?  
Besides the possibilities introduced via the Command Palette, this package offers clever, or "Expandable", shortcuts (as well as the creation of relatives paths based on them); potentially saving you from having to rummage around to set your clipboard for longer trees.  
It also allows for custom opening schemes such as always opening in a new/previous/original window.
To get a feel for this, look at the [mockup](./resources/mockup.json).