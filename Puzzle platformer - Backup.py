"""
Platformer Game
"""
import arcade

# Constants for the screen that the game is played in
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Platformer"

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

# Layer names from our tilemap
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_BOUNCE = "Bounce"
LAYER_NAME_DONT_TOUCH = "Dont touch"
LAYER_NAME_EXIT_SIGN = "Exit sign"
LAYER_NAME_LOCKS = "Locks"
LAYER_NAME_LADDERS = "Ladders"
LAYER_NAME_KEY = "Key"
LAYER_NAME_PLACEHOLDER = "Placeholder"

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
        self.animate = "Idle"

        # Sets the constants for animation type and animation number
        self.animation_num = "1"

        # --- Load Textures ---

        # Images from Kenney.nl's Asset Pack 3
        main_path = f"C:/Users/kevin/Documents/School/13DTP/character_animations/{self.animate}({self.animation_num}).png"

        # Load textures for idle standing
        self.idle_texture_pair = (f"{main_path}")
        self.jump_texture_pair = (f"{main_path}")

        # Load textures for walking
        self.walk_textures = []
        for i in range(14):
            texture = (f"{main_path}_walk{i}.png")
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


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Our TileMap Object
        self.tile_map = None

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

        # Keep track of the score
        self.score = 0

        # Keeps track of the coins collected
        self.coin_list = None

        # Multiple levels and two timelines
        self.level = 1
        self.timeline = 1

        # Sets the timeline_change variable to 0, showing the timeline hasn't changed yet.
        self.timeline_change = 0

        # Sets the constants for yellow keys and locks
        self.lock_state = LAYER_NAME_LOCKS
        self.key_claim = 0

        self.animate = None

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

        # Sets the background colour of the maps
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        # Setup the Cameras
        self.camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        # Name of map file to load
        map_name = f"C:/Users/kevin/Documents/School/13DTP/game_level_{self.level}_{self.timeline}.tmx"

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

            }}}}}},

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Sets up the character and scales them accordingly
        
    
        
        # Adds the player sprite into the game
        self.scene.add_sprite("Player", self.player_sprite)

        # The character is placed at these coordinates when they spawn at the beginning.
        # When the timeline_change = 0, it means the player has just run the code and
        # will spawn at the starting coordinates.

        if self.timeline_change == 0:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

        # When the timeline changes, the player wil preserve their position
        # from the old/new timeline into the current timeline.

        elif self.timeline_change > 0:
            self.player_sprite.center_x = self.position_x 
            self.player_sprite.center_y = self.position_y 
            
        # --- Other stuff
        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        self.physics()
    
    # A seperate function for the physics engine in order to refer to it when collecting keys
    def physics(self):

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, 
            platforms=self.scene[LAYER_NAME_PLATFORMS],
            walls=self.scene[self.lock_state],
            ladders=self.scene[LAYER_NAME_LADDERS]
            )

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





    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
            elif self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        elif key == arcade.key.DOWN or key == arcade.key.S:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

        # The user presses Z or Q to switch between timelines.
        if key == arcade.key.Z or key == arcade.key.Q:
            
            # If the player is in the snow timeline:
            # Preserve the players' location and change or increment the relevant variables.
            if self.timeline == 1:
                self.position_x = self.player_sprite.center_x
                self.position_y = self.player_sprite.center_y
                self.timeline += 1
                self.timeline_change += 1
                self.key_claim = 0
                self.lock_state = LAYER_NAME_LOCKS
                self.setup()

            # If the player is in the grass timeline:
            # Preserve the players' location and change or increment the relevant variables.
            elif self.timeline == 2:
                self.position_x = self.player_sprite.center_x
                self.position_y = self.player_sprite.center_y
                self.timeline -= 1
                self.timeline_change += 1
                self.key_claim = 0
                self.lock_state = LAYER_NAME_LOCKS
                self.setup()
        
        if key == arcade.key.R:
            self.timeline_change = 0
            self.key_claim = 0
            self.lock_state = LAYER_NAME_LOCKS
            self.setup()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

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

    def update(self, delta_time):
        """Movement and game logic"""

        # Move the player with the physics engine
        self.physics_engine.update()

                # Update animations
        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        if self.physics_engine.is_on_ladder() and not self.physics_engine.can_jump():
            self.player_sprite.is_on_ladder = True

        else:
            self.player_sprite.is_on_ladder = False


        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_KEY]
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
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            
        # Checks if the player falls off the map

        if self.player_sprite.center_y < 1:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

        # Checks if the player finishes a level (hits an exit sign), moving them to
        # the next level.

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_EXIT_SIGN]
        ):
            self.level += 1
            self.timeline_change = 0
            self.setup()


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

        
  


        # Centers the camera on the player 

        self.center_camera_to_player()


def main():
    """Main function"""
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()