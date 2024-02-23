"""Puzzle Platformer Game"""
import os
import arcade
import arcade.gui

# Set the title and constants for screen dimensions and the line
# length disparity for body text for the instructions screen.
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Puzzle Platformer"
DEFAULT_LINE_HEIGHT = 45

# Sets the constants to scale our character in proportion to the map.
CHARACTER_SCALING = 0.5
TILE_SCALING = 0.4
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Sets the movement constants and starting position of the player.
PLAYER_MOVEMENT_SPEED = 10
GRAVITY = 1.2
PLAYER_JUMP_SPEED = 20
PLAYER_START_X = 128
PLAYER_START_Y = 286

# Sets the amount of pixels to keep as a minimum margin between the
# character and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 200
RIGHT_VIEWPORT_MARGIN = 200
BOTTOM_VIEWPORT_MARGIN = 150
TOP_VIEWPORT_MARGIN = 100

# Integers used to track if the player is facing left or right.
RIGHT_FACING = 0
LEFT_FACING = 1

# Layer names from our tilemap so they can be refered to later on.
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_BOUNCE = "Bounce"
LAYER_NAME_DONT_TOUCH = "Dont touch"
LAYER_NAME_EXIT_SIGN = "Exit sign"
LAYER_NAME_LOCKS = "Locks"
LAYER_NAME_LADDERS = "Ladders"
LAYER_NAME_KEY_1 = "Key1"
LAYER_NAME_KEY_2 = "Key2"
LAYER_NAME_PLACEHOLDER = "Placeholder"
LAYER_NAME_PLAYER = "Player"
LAYER_NAME_POTION_1 = "Potion1"
LAYER_NAME_POTION_2 = "Potion2"


def load_texture_pair(filename):
    """Load a texture pair for the player character's left and right"""
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class PlayerCharacter(arcade.Sprite):
    """Player Sprite class for player animations"""

    def __init__(self):
        """Allows the class to run object oriented attributes"""

        # Returns an object that represents a parent class.
        super().__init__()

        # Sets the player sprites default position to face-right.
        self.character_face_direction = RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Create variables to track the state of the player sprite.
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

        # Refers to player sprite from Kenney.nl's Asset Pack 3.
        main_path = (":resources:images/\
animated_characters/male_adventurer/maleAdventurer")

        # Loads the textures for idle standing.
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Loads the textures for walking.
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Loads the textures for climbing.
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial textures.
        self.texture = self.idle_texture_pair[0]

        # Sets the player sprites hitbox based on the stationary
        # position of the player sprite.
        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):
        """Updates animations depending on what the player
        does at a given time"""

        # Determines whether the player sprite is facing left or right.
        if self.change_x < 0 and \
        self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and \
        self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Sets the climbing animations for ladders.
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

        # Sets the jumping animations for when the character jumps.
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = \
            self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = \
            self.fall_texture_pair[self.character_face_direction]
            return

        # Sets the players' idle animation.
        if self.change_x == 0:
            self.texture = \
            self.idle_texture_pair[self.character_face_direction]
            return

        # Sets the players walking animation.
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction]


class GameView(arcade.View, PlayerCharacter):
    """Game view class for when the game is playing"""

    def __init__(self):
        """Allows the class to run object oriented attributes"""

        # Returns an object that represents a parent class.
        super().__init__()
        
        # Creates a variable for our tile map.
        self.tile_map = None

        # Sets the path to run the game view.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Creates variables to track the current 
        # state of what key is pressed.
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False

        # Creates a variable for our scene object.
        self.scene = None

        # Creates a variable that holds the player sprite.
        self.player_sprite = None

        # Creates a variable for our physics engine.
        self.physics_engine = None

        # Assigns a variable for a camera to scroll the screen.
        self.camera = None

        # Assigns a variable for a Camera that can be 
        # used to draw GUI elements.
        self.gui_camera = None
        
        # Creates variable for multiple levels and two timelines.
        self.level = 1
        self.timeline = 1

        # Sets the timeline_change variable to 0
        # showing the timeline hasn't changed yet.
        self.timeline_change = 0

        # Sets the constant for locks and variables for if the yellow
        # key(s) has been claimed and whether they are available
        # for use.
        self.lock_state = LAYER_NAME_LOCKS
        self.keys_available = 0
        self.key_claim_1 = 0
        self.key_claim_2 = 0

        # Sets the variables for the number of potions the user has
        # collected and whether they are available for use.
        self.potions_available = 0
        self.potion_claim_1 = 0
        self.potion_claim_2 = 0
        
        # Assigns a variabele for the direction the player sprite is
        # facing, so we can refer to it for this class.
        self.character_face_direction = \
        PlayerCharacter().character_face_direction
        
        # Load sounds to play when doing applicable activities.
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

        self.setup()

    def setup(self):
        """This function is called whenever the 
        game needs to be setup"""
  
        # Setup the cameras.
        self.camera = arcade.Camera()
        self.gui_camera = arcade.Camera()

        # Closes the game if the player beats level 3
        if self.level > 3:
            arcade.exit()

        # Name of map file to load, along with the relevant level and 
        # timeline to load to allow for easy switching between
        # levels and timelines.
        self.map_name = f"C:/Users/kevin/Documents/School/13DTP/\
game_level_{self.level}_{self.timeline}.tmx"

        # Layer specific options make the SpriteList for the platforms 
        # layer, with spatial hashing used for detection.
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            LAYER_NAME_DONT_TOUCH: {
                "use_spatial_hash": True,
            LAYER_NAME_LOCKS: {
                "use_spatial_hash": True,
            LAYER_NAME_LADDERS: {
                "use_spatial_hash": False,
            LAYER_NAME_KEY_1: {
                "use_spatial_hash": False,
            LAYER_NAME_KEY_2: {
                "use_spatial_hash": False,          

            }}}}}}},

        # Loading the tiled map.
        self.tile_map = arcade.load_tilemap(self.map_name, 
        TILE_SCALING, layer_options)

        # Use scene to load up all layers from the map as SpriteLists 
        # in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
    
        # Sets up the character and the starting coordinates 
        # and scales them accordingly.
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite(LAYER_NAME_PLAYER, self.player_sprite)

        # The character is placed at these coordinates when they spawn
        # at the beginning.
        # When the timeline_change = 0, it means the player has just 
        # started the level and will spawn at the starting coordinates.
        if self.timeline_change == 0:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

        # When the timeline changes, the player wil preserve their 
        # position from the grass/snow timeline into the 
        # current timeline.
        elif self.timeline_change > 0:
            self.player_sprite.center_x = self.position_x 
            self.player_sprite.center_y = self.position_y

        # Updates the physics engine whenever setup is run.
        self.physics()
    
    def physics(self):
        """A seperate function for the physics engine in order to 
        update to it when necessary."""

        # Create the physics engine for the object oriented programming
        # which sets the gravity constant and specific collision
        # types for specific objects.
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, 
            platforms=self.scene[LAYER_NAME_PLATFORMS],
            walls=self.scene[self.lock_state],
            ladders=self.scene[LAYER_NAME_LADDERS]
            )

    def on_show(self):
        """Runs the setup function when the game screen is shown"""
        self.setup()

    def on_draw(self):
        """Renders the screen and draws the applicable text"""

        # Clear the screen of anything from previous screens.
        self.clear()

        # Activates the game camera.
        self.camera.use()

        # Draws our Scene.
        self.scene.draw()

        # Refers to the GUI camera to draw GUI elements.
        self.gui_camera.use()

        # Creates a counter on screen for potions the player can use.
        potions_available = f"Potions: {self.potions_available}"
        arcade.draw_text(
            potions_available,
            50,
            50,
            arcade.csscolor.WHITE,
            20,
        )

        # Creates a counter on screen for keys the player can use.
        keys_available = f"Keys: {self.keys_available}"
        arcade.draw_text(
            keys_available,
            50,
            75,
            arcade.csscolor.WHITE,
            20,
        )

    def process_keychange(self):
        """A function for when we move up/down/left/right
        or we move on/off a ladder"""

        # Creates the users ability to move up and down
        # with reference to objects.
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

        # Creates the users ability to move up and down 
        # when on a ladder and with no movement.
        if self.physics_engine.is_on_ladder():
            if not self.up_pressed and not self.down_pressed:
                self.player_sprite.change_y = 0
            elif self.up_pressed and self.down_pressed:
                self.player_sprite.change_y = 0

        # Creates the users ability to move left and right
        # with reference to player movement speed.
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
        """Whenever a certain key is pressed, 
        a resulting action will occur"""

        # Allows the movement keys of the player sprite.
        if key == arcade.key.UP or key == arcade.key.W \
        or key == arcade.key.SPACE:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
            self.facing_forward = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
            self.facing_forward = True

        # Refer back to this function to process how far they will
        # travel or how they will move on ladders.
        self.process_keychange()

        # The user presses Z or Q to switch between timelines.
        if key == arcade.key.Z or key == arcade.key.Q:
            
            # If the player is in the snow timeline:
            # Preserve the players' location 
            # and change or increment the relevant variables
            # When they switch to the grass timeline.
            if self.timeline == 1:
                self.position_x = self.player_sprite.center_x
                self.position_y = self.player_sprite.center_y
                self.timeline += 1
                self.timeline_change += 1
                self.setup()

            # If the player is in the grass timeline:
            # Preserve the players' location 
            # and change or increment the relevant variables
            # When they switch to the snow timeline.
            elif self.timeline == 2:
                self.position_x = self.player_sprite.center_x
                self.position_y = self.player_sprite.center_y
                self.timeline -= 1
                self.timeline_change += 1
                self.keys_available = 0
                self.lock_state = LAYER_NAME_LOCKS
                self.setup()
 
        # Restarts the level completely, as if the user were to run
        # the code from scratch again.
        if key == arcade.key.R:
            self.timeline_change = 0
            self.keys_available = 0
            self.potions_available = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()

        # Allows the player sprite to teleport a short distance forward
        # depending on what direction they are facing or moving in
        # and whether they have potions to do so.
        if key == arcade.key.E and self.potions_available > 0:
            self.potions_available -= 1
            if self.facing_forward == True:
                self.player_sprite.center_x += 200
            elif self.facing_forward == False:
                self.player_sprite.center_x -= 200
                
    def on_key_release(self, key, modifiers):
        """A function for when the user releases a key"""

        # Stops the applicable movement when the user releases a key.
        if key == arcade.key.UP or key == arcade.key.W \
        or key == arcade.key.SPACE:
            self.up_pressed = False
            self.jump_needs_reset = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        # Refer back to this function to process how far they will
        # travel or how they will move on ladders.
        self.process_keychange()

    def center_camera_to_player(self):
        """Centers the camera on the player"""

        # Centers the camera on the player sprite,
        # subtracting half the viewport width and height.
        screen_center_x = self.player_sprite.center_x - (
            self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2)
       
        # Accounts for the edges of the screen
        # and centers the camera accordingly.
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        """Updates the relevant game objects 
        and player sprite interactions"""

        # Moves the player with regards to the physics engine.
        self.physics_engine.update()

        # Centers the camera on the player. 
        self.center_camera_to_player()

        # Updates animations when the player sprite jumps
        # or climbs ladders.
        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        if self.physics_engine.is_on_ladder() \
        and not self.physics_engine.can_jump():
            self.player_sprite.is_on_ladder = True
            self.process_keychange()
        else:
            self.player_sprite.is_on_ladder = False
            self.process_keychange()

        # Update animations with respect to time and the player sprite.
        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER]
        )

        # Checks if the player hits a trampoline 
        # and bounces them up higher than a regular jump would.
        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_BOUNCE]
         ):
            self.player_sprite.change_y = 30

        # Checks if the player hits a hazard and moves them back to the 
        # starting position while reseting the level.
        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_DONT_TOUCH]
        ):
            self.timeline_change = 0
            self.key_claim_1 = 0
            self.key_claim_2 = 0
            self.keys_available = 0
            self.potions_available = 0
            self.potion_claim_1 = 0
            self.potion_claim_2 = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()
            
        # Checks if the player falls off the map 
        # and restarts the level.
        if self.player_sprite.center_y < 1:
            self.timeline_change = 0
            self.key_claim_1 = 0
            self.key_claim_2 = 0
            self.keys_available = 0
            self.potions_available = 0
            self.potion_claim_1 = 0
            self.potion_claim_2 = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()

        # Checks if the player finishes a level (hits an exit sign),
        # moving them to the next level.
        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_EXIT_SIGN]
        ):
            self.level += 1
            self.timeline_change = 0
            self.potion_claim_1 = 0
            self.potion_claim_2 = 0
            self.key_claim_1 = 0
            self.key_claim_2 = 0
            self.setup()

        # Checks if the user touches key number 1 of any given map,
        # removing it and updating the relevant variables.
        key_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_KEY_1]
        )

        if self.key_claim_1 == 0:

            for key in key_hit_list:
                self.keys_available += 1
                self.key_claim_1 += 1
                key.remove_from_sprite_lists()
                self.lock_state = LAYER_NAME_PLACEHOLDER
                self.physics()
    
        if self.key_claim_1 == 1:
  
            for key in key_hit_list:
                key.remove_from_sprite_lists()

        # Checks if the user touches key number 2 of any given map,
        # removing it and updating the relevant variables.  
        key_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_KEY_2]
        )

        if self.key_claim_2 == 0:

            for key in key_hit_list:
                self.keys_available += 1
                self.key_claim_2 += 1
                key.remove_from_sprite_lists()
                self.lock_state = LAYER_NAME_PLACEHOLDER
                self.physics()
    
        if self.key_claim_2 == 1:

            for key in key_hit_list:
                key.remove_from_sprite_lists()

        # Removes any locks the player collides with, provided that
        # they have a key available.
        lock_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_LOCKS]
        )

        for locks in lock_hit_list:
            locks.remove_from_sprite_lists()

        # Checks if the user touches potion number 1 of any given map,
        # removing it and updating the relevant variables.  
        self.potion_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_POTION_1]
        )

        if self.potion_claim_1 == 0:

            for self.potions in self.potion_hit_list:
                self.potion_claim_1 += 1
                self.potions_available += 1
                self.potions.remove_from_sprite_lists()
            
        if self.potion_claim_1 == 1:

            for self.potions in self.potion_hit_list:
                self.potions.remove_from_sprite_lists()

        # Checks if the user touches potion number 2 of any given map,
        # removing it and updating the relevant variables.     
        self.potion_hit_list = arcade.check_for_collision_with_list(
        self.player_sprite, self.scene[LAYER_NAME_POTION_2]
        )

        if self.potion_claim_2 == 0:

            for self.potions in self.potion_hit_list:
                self.potion_claim_2 += 1
                self.potions_available += 1
                self.potions.remove_from_sprite_lists()

        if self.potion_claim_2 == 1:

            for self.potions in self.potion_hit_list:    
                self.potions.remove_from_sprite_lists()
  

class InstructionsView(arcade.View):
    """A class for the instructions window of the game"""

    def __init__(self):
        """Allows the class to run object oriented attributes"""

        # Returns an object that represents a parent class.
        super().__init__()

        # Create the UIManager to handle the user interface.
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Create a vertical BoxGroup to align buttons.
        self.v_box = arcade.gui.UIBoxLayout()

        # Create a start button for starting the game.
        start_button = arcade.gui.UIFlatButton(text="Start", width=200)
        self.v_box.add(start_button.with_space_around(top=675))
        start_button.on_click = self.on_click_start

        # Create a main menu button for returning to the main menu.
        main_menu_button = arcade.gui.UIFlatButton(text="Main Menu",
        width=200)
        self.v_box.add(main_menu_button.with_space_around(top=20))
        main_menu_button.on_click = self.on_click_main_menu

        # Create a v_box widget to centre the buttons.
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
            )

    def on_show(self):
        """Showing a blue background when we switch to 
        the instructions view"""
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def on_draw(self):
        """Drawing the applicable text when the user 
        is on the instructions page"""

        # Clear any previous visuals on the screen 
        # and draw the new visuals/text.
        self.clear()
        self.manager.draw()

        # Create the starting coordinates to use as a reference point
        # for the text and begin drawing the text.
        start_x = 0
        start_y = 800
        arcade.draw_text("Instructions Screen", start_x, start_y,
                         arcade.color.WHITE, font_size=50, width = 
                         SCREEN_WIDTH, align = "center")

        start_y -= 100
        arcade.draw_text(" - Use WASD or arrow keys to move and jump",
                        start_x, start_y, arcade.color.WHITE, font_size=20, 
                        width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- There are two timelines, \
press Q or Z to swap between them",
start_x, start_y, arcade.color.WHITE, font_size=20, 
width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Press R to restart the level", start_x, start_y,
                        arcade.color.WHITE, font_size=20, 
                        width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Press E to teleport a short distance forward, \
if you collect a potion",
start_x, start_y, arcade.color.WHITE, font_size=20, 
width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Grass and snow blocks indicate that the specific \
tile exists in both timelines", start_x, start_y,
arcade.color.WHITE, font_size=20, 
width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Purple blocks are only available in the \
current timeline", start_x, start_y, 
arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Keys will freeze if travelling from the \
grass timeline to snow timeline", start_x, start_y, 
arcade.color.WHITE, font_size=20, width = SCREEN_WIDTH, align = "left")

        start_y -= DEFAULT_LINE_HEIGHT
        arcade.draw_text("- Get to the exit sign at each level! \
It doesn't matter which timeline you exit in", 
start_x, start_y, arcade.color.WHITE, font_size=20, 
width = SCREEN_WIDTH, align = "left")  
                                                                
    def on_click_start(self, event):
        """If the user presses the start button, 
        the game will commence"""
        game_view = GameView()
        self.window.show_view(game_view)

    def on_click_main_menu(self, event):
        """ If the user presses the main menu button, 
        they will return to the main menu """
        start_view = MainMenu()
        self.window.show_view(start_view)

    def on_hide_view(self):
        """Disables the buttons from the main menu screen 
        to make room for the instructions"""
        self.manager.disable()


class MainMenu(arcade.View):
    """Create a class for the main menu"""

    def __init__(self):
        """Allows the class to run object oriented attributes"""

        # Returns an object that represents a parent class.
        super().__init__()

        # Create a UIManager to handle the user interface.
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Sets the blue background colour.
        arcade.set_background_color(arcade.color.CORNFLOWER_BLUE)

        # Create a vertical BoxGroup to align buttons.
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the start, instructions and quit button.
        start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.v_box.add(start_button.with_space_around(bottom=20))
        start_button.on_click = self.on_click_start

        instructions_button = arcade.gui.UIFlatButton(text="Instructions",
                                                    width=200)
        self.v_box.add(instructions_button.with_space_around(bottom=20))
        instructions_button.on_click = self.on_click_instructions

        quit_button = arcade.gui.UIFlatButton(text="Quit", width=200)
        self.v_box.add(quit_button.with_space_around(bottom=20))
        quit_button.on_click = self.on_click_quit

        # Create a v_box widget to centre the buttons.
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
            )

    def on_click_start(self, event):
        """Switches to the game view when the user clicks start"""
        game_view = GameView()
        self.window.show_view(game_view)
        arcade.run()

    def on_click_instructions(self, event):
        """Switches to the instructions screen when 
        the user clicks instructions"""
        instructions_view = InstructionsView()
        self.window.show_view(instructions_view)
        arcade.run()

    def on_click_quit(self, event):
        """Closes the game when the user clicks on quit"""
        arcade.exit()

    def on_draw(self):
        """Drawing the applicable text when the user 
        is on the main menu page"""
        self.clear()
        self.manager.draw()

    def on_hide_view(self):
        """Disables any buttons drawn from previous screens"""
        self.manager.disable()


def main():
    """Main function which runs whenever the code begins,
    putting the user at the main menu screen."""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = MainMenu()
    window.show_view(start_view)
    arcade.run()

# Run the main function on startup.
if __name__ == "__main__":
    main()