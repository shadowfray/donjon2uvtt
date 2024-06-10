# Donjon 2 Universal VTT
This is a simple script to change a generated [Donjon Dungeon](https://donjon.bin.sh/d20/dungeon/) to [Universal VTT format](https://github.com/moo-man/FVTT-DD-Import/tree/master) to be uploaded in Foundry VTT. This file only recreates the dungeon as a basic black and white PNG, automatically creating wall and door data. This works for all dungeons generated by their website as far as I can tell.

## Running the script
You will need python installed, then just run the script. It will prompt you for the Donjon JSON, and will give you a Universal VTT file, along with a PNG of the dungeon.

## Features
- Packages a minimal PNG recreation of the dungeon into the Universl VTT file
- Places wall data for all walls
- Places door data for all doors
  - Doors, regardless if they are a door, portcullis or locked door are simply treated as doors right now
  - Secret doors are placed as walls on both sides. You'll likely want to pick one side to be the "True" secret door and delete the other by hand.
  - Archways are added to the underlying PNG
- Places stairs, though there is no visual distinction between up and down stairs
- All other features that would be visible on the map are not present
- No data such as room descriptions, lights, encounters, etc are preserved from the JSON

## Future Plans:
- Package as an executable so you don't need python to run it
- Investigate if UVTT files can contain transparent doors and locked doors
  - Make Locked Doors start locked
  - Make all Portcullises doors transparent
  
