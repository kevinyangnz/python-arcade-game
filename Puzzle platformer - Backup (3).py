"""
Platformer Game
"""
import os
import arcade
import arcade.gui


# Constants for the screen that the game is played in
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Platformer"
DEFAULT_LINE_HEIGHT = 45

# Constants used to scale our sprites from their original size
CHARACTER_SCALING = 0.5
TILE_SCALING = 0.4
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 10
GRAVITY = 1.2
PLAYER_JUMP_SPEED = 20
PLAYER_START_X = 128
PLAYER_START_Y = 286

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 200
RIGHT_VIEWPORT_MARGIN = 200
BOTTOM_VIEWPORT_MARGIN = 150
TOP_VIEWPORT_MARGIN = 100

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

# Layer names from our tilemap
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_BOUNCE = "Bounce"
LAYER_NAME_DONT_TOUCH = "Dont touch"
LAYER_NAME_EXIT_SIGN = "Exit sign"
LAYER_NAME_LOCKS = "Locks"
LAYER_NAME_LADDERS = "Ladders"
LAYER_NAME_KEY = "Key"
LAYER_NAME_PLACEHOLDER = "Placeholder"
LAYER_NAME_PLAYER = "Player"
LAYER_NAME_TELEPORT_POTION = "Teleport potion"



def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]

class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

        # --- Load Textures ---

        # Images from Kenney.nl's Asset Pack 3
        main_path = ":resources:images/animated_characters/male_adventurer/maleAdventurer"

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used. If you want to specify
        # a different hit box, you can do it like the code below.
        # set_hit_box = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Climbing animation
        if self.is_on_ladder:
            self.climbing = True
        if not self.is_on_ladder and self.climbing:
            self.climbing = False
        if self.climbing and abs(self.change_y) > 1:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
        if self.climbing:
            self.texture = self.climbing_textures[self.cur_texture // 4]
            return

        # Jumping animation
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction
        ]



class GameView(arcade.View, PlayerCharacter):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__()
        

        # Our TileMap Object
        self.tile_map = None

        # Set the path to start with this program
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False

        # Our Scene Object
        self.scene = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None


        # A Camera that can be used for scrolling the screen
        self.camera = None

        # A Camera that can be used to draw GUI elements
        self.gui_camera = None
        
        self.sprite_lists = [LAYER_NAME_TELEPORT_POTION]

        # Multiple levels and two timelines
        self.level = 1
        self.timeline = 1

        # Sets the timeline_change variable to 0, showing the timeline hasn't changed yet.
        self.timeline_change = 0

        # Sets the constant for locks and variable for if the yellow key(s) has been claimed.
        self.lock_state = LAYER_NAME_LOCKS
        self.key_claim = 0

        # Sets the variable for the number of potions the user has collected
        self.potion_claim = 0
        self.character_face_direction = PlayerCharacter().character_face_direction
        

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

        # Sets the background colour of the maps
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)


    def setup(self):
        """Set up the game here. Call this function to restart the game."""
  
        # Setup the Cameras
        self.camera = arcade.Camera()
        self.gui_camera = arcade.Camera()

        # Name of map file to load
        self.map_name = f"C:/Users/kevin/Documents/School/13DTP/game_level_{self.level}_{self.timeline}.tmx"

        # Layer specific options are defined based on Layer names in a dictionary
        # Doing this will make the SpriteList for the platforms layer
        # use spatial hashing for detection.
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            LAYER_NAME_DONT_TOUCH: {
                "use_spatial_hash": True,
            LAYER_NAME_LOCKS: {
                "use_spatial_hash": True,
            LAYER_NAME_LADDERS: {
                "use_spatial_hash": False,
            LAYER_NAME_KEY: {
                "use_spatial_hash": False,
            LAYER_NAME_TELEPORT_POTION: {
                "use_spatial_has": False,

            }}}}}}},

        # Loading the tiled map
        self.tile_map = arcade.load_tilemap(self.map_name, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Sets up the character and scales them accordingly
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite(LAYER_NAME_PLAYER, self.player_sprite)

        # The character is placed at these coordinates when they spawn at the beginning.
        # When the timeline_change = 0, it means the player has just started the level and
        # will spawn at the starting coordinates.

        if self.timeline_change == 0:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

        # When the timeline changes, the player wil preserve their position
        # from the old/new timeline into the current timeline.

        elif self.timeline_change > 0:
            self.player_sprite.center_x = self.position_x 
            self.player_sprite.center_y = self.position_y
            self.remove_sprite_list_by_name()


          
        # --- Other stuff
        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        self.physics()
    
    # A seperate function for the physics engine in order to update to it when necessary.
    def physics(self):

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, 
            platforms=self.scene[LAYER_NAME_PLATFORMS],
            walls=self.scene[self.lock_state],
            ladders=self.scene[LAYER_NAME_LADDERS]
            )

    def remove_sprite_list_by_name(self):

        if self.potion_claim > 0:

            self.potion_hit_list = arcade.remove(
            self.player_sprite, self.scene[LAYER_NAME_TELEPORT_POTION]
            )

            for self.potions in self.potion_hit_list:

                self.potions.remove_from_sprite_lists()



    def on_show(self):
        self.setup()

    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Activate the game camera
        self.camera.use()

        # Draw our Scene
        self.scene.draw()

        # Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

        potions_available = f"Potions: {self.potion_claim}"
        arcade.draw_text(
            potions_available,
            50,
            50,
            arcade.csscolor.WHITE,
            20,
        )

        keys_available = f"Keys: {self.key_claim}"
        arcade.draw_text(
            keys_available,
            50,
            75,
            arcade.csscolor.WHITE,
            20,
        )


    def process_keychange(self):
        """
        Called when we change a key up/down or we move on/off a ladder.
        """
        # Process up/down
        if self.up_pressed and not self.down_pressed:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
            elif (
                self.physics_engine.can_jump(y_distance=10)
                and not self.jump_needs_reset
            ):
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)
        elif self.down_pressed and not self.up_pressed:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED

        # Process up/down when on a ladder and no movement
        if self.physics_engine.is_on_ladder():
            if not self.up_pressed and not self.down_pressed:
                self.player_sprite.change_y = 0
            elif self.up_pressed and self.down_pressed:
                self.player_sprite.change_y = 0

        # Process left/right
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0



    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
            self.facing_forward = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
            self.facing_forward = True

        if key == arcade.key.PLUS:
            self.camera.zoom(0.01)
        elif key == arcade.key.MINUS:
            self.camera.zoom(-0.01)
        
        self.process_keychange()

        # The user presses Z or Q to switch between timelines.
        if key == arcade.key.Z or key == arcade.key.Q:
            
            # If the player is in the snow timeline:
            # Preserve the players' location and change or increment the relevant variables
            # When they switch to the grass timeline.
            if self.timeline == 1:
                self.position_x = self.player_sprite.center_x
                self.position_y = self.player_sprite.center_y
                self.timeline += 1
                self.timeline_change += 1

                self.setup()

            # If the player is in the grass timeline:
            # Preserve the players' location and change or increment the relevant variables
            # When they switch to the snow timeline.
            elif self.timeline == 2:
                self.position_x = self.player_sprite.center_x
                self.position_y = self.player_sprite.center_y
                self.timeline -= 1
                self.timeline_change += 1

                # Currently the only difference between snow and grass. Resets locks since they move
                # from future to past
                self.key_claim = 0
                self.lock_state = LAYER_NAME_LOCKS
                self.setup()
        
        if key == arcade.key.R:
            self.timeline_change = 0
            self.key_claim = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()

        if key == arcade.key.E and self.potion_claim > 0:
            self.potion_claim -= 1
            if self.facing_forward == True:
                self.player_sprite.center_x += 200
            elif self.facing_forward == False:
                self.player_sprite.center_x -= 200
                

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            self.up_pressed = False
            self.jump_needs_reset = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        self.process_keychange()

 
    def center_camera_to_player(self):
        
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        """Movement and game logic"""

        if self.timeline_change > 0:
            self.remove_sprite_list_by_name()


        # Move the player with the physics engine
        self.physics_engine.update()

        # Centers the camera on the player 
        self.center_camera_to_player()


        # Update animations
        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        if self.physics_engine.is_on_ladder() and not self.physics_engine.can_jump():
            self.player_sprite.is_on_ladder = True
            self.process_keychange()
        else:
            self.player_sprite.is_on_ladder = False
            self.process_keychange()

        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER]
        )

        # Checks if the player hits a trampoline and bounces them up

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_BOUNCE]
         ):
            self.player_sprite.change_y = 30

        # Checks if the player hits a hazard, and moves them back to the starting position

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_DONT_TOUCH]
        ):
            self.timeline_change = 0
            self.key_claim = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()
            
        # Checks if the player falls off the map and restarts the level.

        if self.player_sprite.center_y < 1:
            self.timeline_change = 0
            self.key_claim = 0
            self.potion_claim = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()

        # Checks if the player finishes a level (hits an exit sign), moving them to
        # the next level.

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_EXIT_SIGN]
        ):
            self.level += 1
            self.timeline_change = 0
            self.setup()

        #

        key_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_KEY]
        )

        for key in key_hit_list:
            key.remove_from_sprite_lists()
            self.key_claim += 1
        
        if self.key_claim == 1:
            self.lock_state = LAYER_NAME_PLACEHOLDER
            self.physics()

        lock_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_LOCKS]
        )

        for locks in lock_hit_list:
            locks.remove_from_sprite_lists()

        # 

        self.potion_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_TELEPORT_POTION]
        )

        for self.potions in self.potion_hit_list:

            self.potion_claim += 1
            self.remove_sprite_list_by_name()

    def remove_sprite_list_by_name(self):

        if self.potion_claim > 0:

            self.potions.remove_from_sprite_lists()
    

class InstructionsView(arcade.View):

    def __init__(self):
        super().__init__()

        # --- Required for all code that uses UI element,
        # a UIManager to handle the UI.
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Set background color
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        start_button = arcade.gui.UIFlatButton(text="Start", width=200)
        self.v_box.add(start_button.with_space_around(top=675))

        start_button.on_click = self.on_click_start

        main_menu_button = arcade.gui.UIFlatButton(text="Main Menu", width=200)
        self.v_box.add(main_menu_button.with_space_around(top=20))

        main_menu_button.on_click = self.on_click_main_menu

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
            )

    def on_show(self):
        """ This is run once when we switch to this view """
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

    def on_draw(self):
        """ Draw this view """
        self.clear()
        self.manager.draw()

        start_x = 0
        start_y = 800
        arcade.draw_text("Instructions Screen", start_x, start_y,
                         arcade.color.WHITE, font_size=50, width = SCREEN_WIDTH, align = "center")

        start_y -= 100
        arcade.draw_text(" - Use WASD or arrow keys to move or jump accordingly", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- There are two timelines, press Q or Z to swap between", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Press R to restart the level", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Grass and snow blocks indicate that the specific tile exists in both timelines", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Purple blocks are only available in the current timeline", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Any keys from the grass timeline will freeze up when taken to the snow timeline", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Get to the exit sign at each level! It doesn't matter which timeline you exit in", start_x, start_y,
                         arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")                               


    def on_click_start(self, event):
        """ If the user presses the next button, start the game. """
        game_view = GameView()
        self.window.show_view(game_view)

    def on_click_main_menu(self, event):
        """ If the user presses the main_menu button, start the game. """
        start_view = MainMenu()
        self.window.show_view(start_view)


    def on_hide_view(self):
        self.manager.disable()


class MainMenu(arcade.View):

    def __init__(self):
        super().__init__()

        # --- Required for all code that uses UI element,
        # a UIManager to handle the UI.
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Set background color
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.v_box.add(start_button.with_space_around(bottom=20))
        

        instructions_button = arcade.gui.UIFlatButton(text="Instructions", width=200)
        self.v_box.add(instructions_button.with_space_around(bottom=20))

        quit_button = arcade.gui.UIFlatButton(text="Quit", width=200)
        self.v_box.add(quit_button.with_space_around(bottom=20))

        

        start_button.on_click = self.on_click_start


        instructions_button.on_click = self.on_click_instructions

        quit_button.on_click = self.on_click_quit

 

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
            )

    def on_click_start(self, event):
        game_view = GameView()
        self.window.show_view(game_view)
        arcade.run()

    def on_click_instructions(self, event):

        instructions_view = InstructionsView()
        self.window.show_view(instructions_view)
        arcade.run()

    def on_click_quit(self, event):
        arcade.exit()

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_hide_view(self):
        self.manager.disable()



def main():
    """Main function"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = MainMenu()
    window.show_view(start_view)
    arcade.run()

if __name__ == "__main__":
    main()