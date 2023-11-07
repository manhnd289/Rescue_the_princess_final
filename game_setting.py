import pygame
import os
from pygame import mixer

mixer.init()
pygame.font.init()



# ====================================================== GAME'S PROPERTIES ====================================================== #
SCREEN_WIDTH = 800                                                         # Thiết lập kích thước màn hình hiển thị
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))       # Tạo cửa sổ hiển thị
pygame.display.set_caption("NHOM_15.Contra_4_Remake")                      # Đặt tên cửa sổ hiển thị

FPS = pygame.time.Clock()           # Thiết lập FPS
SCROLL_TRIGGER = 200                # Khoảng cách từ player đến cạnh của cửa sổ hiện thị để camera bắt đầu cuộn
BG_SCROLL = 0                       # Offset của background so với trục tọa độ ban đầu
SCREEN_SCROLL = 0                   # Offset của các object so với player khi player di chuyển
OFFSET_BG_MENU = 0                  # Kiểm soạt độ dịch chuyển ở menu bắt đầu
START_GAME = False                  # Bắt đầu game sau khi thoát khỏi menu
START_INTRO = False                 # Hiệu ứng chuyển cảnh khi bắt đầu hoặc restart
ROWS = 16 ; COLS = 150              # Grid map để set tiles map - Level Editor
level = 1 ; MAX_LEVELS = 2          # Level game
TILE_SIZE = SCREEN_HEIGHT // ROWS   # Set kích thước 1 tile theo số hàng
VIDEO_PLAYED = False                # Kiểm soát việc cho phép chạy video khi hoàn thành hết màn chơi
TILE_TYPES = len(os.listdir(os.path.join('Assets','Image','tile')))         # Số kiểu tile

# GUI
font_1 = pygame.font.Font(os.path.join("Assets",'PIXELADE.ttf'),30); font_1.set_bold(True)
font_2 = pygame.font.Font(os.path.join("Assets",'PIXELADE.ttf'),20)
RED = (255, 0, 0)
BG_COLOR = (144, 201,120)
WHITE = (255,255,255)
GREEN = (0,255,0)
BLACK = (0,0,0)
PINK = (235, 65, 54)
TEXT_COLOR = (108, 126, 225)



# ====================================================== PLAYER'S PROPERTIES ====================================================== #

GRAVITY = 1                 # Gia tốc rơi tự do
ANIM_COOLDOWN = 100         # Thiết lập thời gian chờ để đổi trạng thái trong 1 action
EXPLOSION_COOLDOWN = 5      # Thời gian chuyển trạng thái của lựu đạn nổ
speed_of_bullet = 10        # Tốc độ đạn là cố định

moving_left = moving_right = False          # Kiểm soát hướng di chuyển của soldier
isShooting = False                          # Kiểm soát các hành động gây sát thương (không cho phép diễn ra liên tục)
is_throwing_grenade = False                
grenade_thrown = False                     



# ====================================================== LOAD ASSETS ====================================================== #

# ICONS IMAGE
bullet_image = pygame.image.load(os.path.join('Assets','Image','icons','bullet.png')).convert_alpha()
bullet_image = pygame.transform.scale_by(bullet_image, 0.5)
grenade_image = pygame.image.load(os.path.join('Assets','Image','icons','grenade.png')).convert_alpha()
ammo_box_image = pygame.image.load(os.path.join('Assets','Image','icons','ammo_box.png')).convert_alpha()
grenade_box_image = pygame.image.load(os.path.join('Assets','Image','icons','grenade_box.png')).convert_alpha()
health_box_image = pygame.image.load(os.path.join('Assets','Image','icons','health_box.png')).convert_alpha()

# BOX DICTIONARY
item_boxes_lst = {
    'Health' : health_box_image,
    'Ammo' : ammo_box_image,
    'Grenade' : grenade_box_image
}

# List tiles đã được căn chỉnh ứng với 1 ô trong grid map của scene
img_tiles_lst = []                                                    
for i in range(TILE_TYPES):
    img = pygame.image.load(os.path.join('Assets','Image','tile',f'{i}.png')).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_tiles_lst.append(img)

# Sprites cho background
sky_img = pygame.image.load(os.path.join('Assets','Image','background','0.png')).convert_alpha()
sky_img = pygame.transform.scale(sky_img, (sky_img.get_width(), sky_img.get_height() + 200))
cloud_img = pygame.image.load(os.path.join('Assets','Image','background','1.png')).convert_alpha()
mountain1_img = pygame.image.load(os.path.join('Assets','Image','background','2.png')).convert_alpha()
mountain1_img = pygame.transform.scale(mountain1_img, (mountain1_img.get_width(), mountain1_img.get_height() + 200))
mountain2_img = pygame.image.load(os.path.join('Assets','Image','background','3.png')).convert_alpha()
mountain2_img = pygame.transform.scale(mountain2_img, (mountain2_img.get_width(), mountain2_img.get_height() + 300))
bg_menu_img = pygame.image.load(os.path.join('Assets','Image','background','pre.png')).convert_alpha()
bg_menu_img = pygame.transform.scale(bg_menu_img, (SCREEN_WIDTH,SCREEN_HEIGHT))
game_over_img = pygame.image.load(os.path.join('Assets','Image','background','game_over.png')).convert_alpha()
game_over_img = pygame.transform.scale(game_over_img, (256,150))



# Nạp asset cho health bar
bg_health_bar_img = pygame.image.load(os.path.join('Assets','Image','health_bar','0.png')).convert_alpha()
bg_health_bar_img = pygame.transform.scale_by(bg_health_bar_img, 0.5)
rect_char_img = pygame.image.load(os.path.join('Assets','Image','health_bar','1.png')).convert_alpha()
rect_char_img_1 = pygame.transform.scale_by(rect_char_img, 1.75)
avt_img = pygame.image.load(os.path.join('Assets','Image','health_bar','2.png')).convert_alpha()
avt_img = pygame.transform.scale_by(avt_img, 1.7)
health_bar_1_img = pygame.image.load(os.path.join('Assets','Image','health_bar','3.png')).convert_alpha()
health_bar_1_img = pygame.transform.scale(health_bar_1_img, (health_bar_1_img.get_width()*3.5, health_bar_1_img.get_height()*2))
# Cần lưu lại thanh máu ban đầu sau khi đã scale chuẩn và tạo đối tượng mới với chỉnh sửa trên thanh máu ban đầu
health_bar_2_img = pygame.image.load(os.path.join('Assets','Image','health_bar','4.png')).convert_alpha()
health_bar_2_img_original = pygame.transform.scale(health_bar_2_img, (health_bar_2_img.get_width()*3.5, health_bar_2_img.get_height()*2))
health_bar_2_img_current = pygame.transform.scale(health_bar_2_img_original, (health_bar_2_img_original.get_width(), health_bar_2_img_original.get_height()))
bullet_bar_img = pygame.image.load(os.path.join('Assets','Image','health_bar','5.png')).convert_alpha()



# Nạp assets cho tutorial
bg_tutorial = pygame.transform.scale(rect_char_img, (SCREEN_WIDTH//2, SCREEN_HEIGHT * 0.8))
n_button_img = pygame.image.load(os.path.join('Assets','Image','tutorial','0.png')).convert_alpha()
space_button_img = pygame.image.load(os.path.join('Assets','Image','tutorial','1.png')).convert_alpha()
esc_button_img = pygame.image.load(os.path.join('Assets','Image','tutorial','2.png')).convert_alpha()
arrow_button_img = pygame.image.load(os.path.join('Assets','Image','tutorial','3.png')).convert_alpha()
char_sample_img = pygame.transform.scale(img_tiles_lst[15], (img_tiles_lst[15].get_width() * 2.3, img_tiles_lst[15].get_height() * 3))



# Các nút cho các lựa chọn trong menu
exit_btn_image = pygame.image.load(os.path.join('Assets','Image','button','exit_btn.png')).convert_alpha()
restart_btn_image = pygame.image.load(os.path.join('Assets','Image','button','restart_btn.png')).convert_alpha()
start_btn_image = pygame.image.load(os.path.join('Assets','Image','button','start_btn.png')).convert_alpha()

# Nạp vào các hiệu ứng âm thanh
jmp_fx = pygame.mixer.Sound(os.path.join('Assets','Audio','jump.mp3'))
jmp_fx.set_volume(0.7)
grenade_fx = pygame.mixer.Sound(os.path.join('Assets','Audio','grenade.wav'))
grenade_fx.set_volume(0.3)
player_shot_fx = pygame.mixer.Sound(os.path.join('Assets','Audio','player_shot.mp3'))
player_shot_fx.set_volume(0.1)
enemy_shot_fx = pygame.mixer.Sound(os.path.join('Assets','Audio','enemy_shot.wav'))
enemy_shot_fx.set_volume(0.1)
game_over_fx = pygame.mixer.Sound(os.path.join('Assets','Audio','game_over.wav'))



# Nhạc nền sẽ được chạy ngay khi khởi động game
pygame.mixer.music.load(os.path.join('Assets','Audio','music.mp3'))
pygame.mixer.music.play(-1, 0.0) # Lặp vô hạn, bắt đầu phát từ đầu đoạn nhạc (1.0 - cuối), đợi 5s trước khi phát nhạc
