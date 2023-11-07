from random import randint
import csv
from button import *
from game_setting import *

pygame.init()           # Khởi tạo game



# ====================================================== CLASSES ====================================================== #

# SỬ DỤNG CHO CẢ PLAYER VÀ ENEMY
class Soldier(pygame.sprite.Sprite):

    def __init__(self, type_of_char, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = type_of_char             # Chọn kiểu nhân vật để nạp ảnh tương ứng
        self.speed = speed                        # Speed các enemy có thể khác nhau
        self.ammo = ammo                          # Lượng đạn hiện thời
        self.start_ammo = ammo                    # Lượng đạn ban đầu (restart không cần khởi tạo lại đối tượng)
        self.grenades = grenades                  # Lượng lựu đạn hiện thời
        self.start_grenades = grenades            # Lượng lựu đạn ban đầu

        self.direction = 1                        # Hướng nhìn của sprite ( 1-phải ; -1:Trái )
        self.health = 100                         # Lượng máu sẽ bị thay đổi
        self.max_health = 100                     # Lượng máu cho cho việc restart
        self.flip = False                         # Kiểm soát lật sprite theo hướng di chuyển
        self.shoot_cooldown = 0                   # Khoảng thời gian cho phép giữa 2 lần bắn
        self.isJumping = False                    # Cập nhật trạng thái nhảy
        self.in_air = True                        # Kiểm soát có đang trong quá trình nhảy hay không
        self.velocity_y = 0                       # Vận tốc rơi tự do
        
        # AI variables - For Enemies
        self.step_cnt = 0                         # Đếm số bước chạy để giới hạn khu vực di chuyển cho enemy
        self.idling = False                       # Kiểm soát action idle khi đang tuần tra
        self.idling_cnt = 0                       # Bộ đếm cho idle sau đó lại chuyển đổi trạng thái tuần tra
        self.vision = pygame.Rect(0,0,150,10)     # Thiết lập tầm nhìn cho enemy để bắt player

        
        self.action = 0                                      # Chọn ra hành động cho character (Default : Idle)
        self.anim_list = []                                  # List các list trạng thái của 1 action
        self.action_types = ['Idle', 'Run', 'Jump', 'Death'] # List các trạng thái của từng hành động ứng với tên folder
        for action in self.action_types:
            status_lst = []                                  # Lưu các trạng thái của từng action
            for i in range(len(os.listdir(os.path.join('Assets', 'Image', self.char_type, action)))):
                img = pygame.image.load(os.path.join('Assets','Image',self.char_type, action, f'{i}.png')).convert_alpha()
                img = pygame.transform.scale(img, (img.get_width()*scale, img.get_height()*scale))
                status_lst.append(img)
            self.anim_list.append(status_lst)                # Nạp nguyên list status vào cuối

        self.update_timer_status = pygame.time.get_ticks()          # Tính toán khoảng thời gian chuyển đổi trạng thái trong 1 action
        self.frame_idx = 0                                          # Chỉ mục cho trạng thái của 1 action
        self.image = self.anim_list[self.action][self.frame_idx]    # Chọn ra ảnh của action và trạng thái của action đó để hiển thị
        self.rect= self.image.get_rect()                            # Tạo khung để xử lý vật lý và hiển thị
        self.rect.center = (x,y)                                  # Vị trí vẽ lên cửa sổ hiển thị
        self.width = self.image.get_width()      
        self.height = self.image.get_height()
        self.cnt_exit = 0                                           # Bộ đếm khi chuẩn bị qua màn không bị quá nhanh
        self.GAME_OVER_FX_PLAYED = False                            # Kiểm soát việc phát âm thanh khi bị chết
        self.key_picked = False                                     # Nhiệm vụ là nhặt chìa khóa thì qua màn


    def move(self, moving_left: bool, moving_right: bool):

        dx = dy = 0
        # Độ dịch chuyển trên trục x,y.
        # Xác định vị trí player sẽ tới chứ chưa xác định ngay vị trí sau va chạm
        
        if moving_left:
            dx = -self.speed
            self.flip = True        # Cần lật ảnh lại vì di chuyển ngược hướng quay mặc định
            self.direction = -1     # Cập nhật hướng di chuyển vẽ đạn
            
        elif moving_right:
            dx = self.speed
            self.flip = False       # Không cần lật vì hướng di chuyển trùng hướng quay mặc định
            self.direction = 1     

        # Nếu nhấn K_UP và đang dưới đất thì bắt đầu chu trình nhảy và kích hoạt trạng thái trên không
        if self.isJumping and not self.in_air:
            self.velocity_y = -15       # Giá trị âm là để nhảy lên
            self.in_air = True          # Chỉ cho phép nhảy 1 lần
        
        
        if self.velocity_y < 10:
            self.velocity_y += GRAVITY  # Cập nhật vận tốc rơi tự do (max = 10)
        dy = self.velocity_y
        
        # Duyệt list các tuple được coi là bề mặt di chuyển
        for tile in world.obstacle_lst:

            # Xét theo vị trí mà player sẽ tới mà không xét theo vị trí hiện tại
            # Va chạm vật cản khi di chuyển - x-axis
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0                      # Không cho di chuyển nữa
                if self.char_type == "enemy":
                    self.direction *= -1    # Chỉ đổi hướng enemies nếu bị chặn bởi tường
                self.step_cnt = 0           # Sau khi đổi hướng sẽ cho action run chạy lại từ đầu

            # Va chạm vật cản khi nhảy - y-axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                dy = 0                      # Không cho di chuyển
                # Nếu đang nhảy lên mà đập đầu vào vật cản thì lập tức rơi xuống
                if self.velocity_y < 0:
                    self.velocity_y = 0     # Set về 0 để bắt đầu rơi xuống
                    dy = tile[1].bottom - self.rect.top
                # Nếu đang rơi xuống thì hủy kích hoạt trên không (nếu không sẽ luôn ở action jump)
                elif self.velocity_y > 0:
                    self.velocity_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # Giới hạn lại khu vực di chuyển của player 
        if self.char_type == "player":
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        # Kiểm tra va chạm với nước
        if pygame.sprite.spritecollide(self,trap_group,False):
            self.health = 0         # Sẽ được cập nhật bởi check_death()
        # Kiểm tra rơi khỏi scene
        if self.rect.bottom  > SCREEN_HEIGHT:
            self.health = 0
        # Kiểm soát qua màn va chạm với cổng nhưng đợi bộ đếm đến 33 mới cho qua không bị quá nhánh
        level_completed = False
        if pygame.sprite.spritecollide(self,exit_group,False) and self.key_picked == True:
            if(self.cnt_exit < 50): self.cnt_exit += 1
            else: level_completed = True
            
        # Cập nhật vị trí player
        self.rect.x += dx
        self.rect.y += dy

        '''
        Chỉ được thực hiện sau khi đã cập nhật vị trí mới của player
        Chỉ khi cuộn thì SCREEN_ROLL mới được cập nhật vì đây là offset so với player
        Trạng thái cuộn màn hình: player đứng yên và các object thì di chuyển theo chiều ngược lại
        '''
        SCREEN_SCROLL = 0
        if self.char_type == "player":
            '''
            Khi player vượt quá màn hình hiển thị và chưa đến cuối scene thì cuộn
            Player không di chuyển mà scene di chuyển, player chỉ đảm bảo hiển thị trong khung hình hiển thị
            Hoặc background đã có sự dịch chuyển rồi mới cho cuộn còn khi ở đầu map giá trị offset này là 0
            '''
            if (self.rect.right > SCREEN_WIDTH - SCROLL_TRIGGER and BG_SCROLL < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) or \
            (self.rect.left < SCROLL_TRIGGER and BG_SCROLL > SCREEN_SCROLL):
                self.rect.x -= dx       # Khi move là sẽ đc += dx và giờ -=dx để player chỉ hiển thị trong window
                SCREEN_SCROLL = -dx     # Độ dịch scene khi player di chuyển

        # Phải trả về vì đây là biến cục bộ thay đổi trong hàm  
        return SCREEN_SCROLL, level_completed

    '''
    User nhấn space, isShooting được kích hoạt (keydown ngay dưới nhưng sẽ không bị hủy ngay lập tức) 
    self.shoot_cooldown kiểm soát việc bắn liên tục trong update()
    Còn đạn và thỏa mãn thời gian đợi bắn thì tạo 1 viên đạn cùng hướng với player và chạy hiệu ứng âm thanh
    '''
    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20            # Set timer cho lần bắn tiếp theo
            bullet_instance = Bullet(self.rect.centerx + (0.6*self.rect.size[0]*self.direction), self.rect.centery + 3, self.direction)
            bullet_group.add(bullet_instance)
            self.ammo -= 1
            if self.char_type == "player": player_shot_fx.play()
            elif self.char_type == "enemy": enemy_shot_fx.play()

    # Kiểm tra hp để cập nhật thuộc tính và action
    def check_death(self):
        if self.health <= 0:
            self.alive = False
            self.health = 0
            self.update_action(3)
            if self.GAME_OVER_FX_PLAYED == False and self.char_type == "player":
                game_over_fx.play(0)
                self.GAME_OVER_FX_PLAYED = True



    def update_action(self, new_action: int):
        # Nếu new_action khác action hiện tại thì cập nhật theo thứ tự đã nạp các action vào anim_list
        # Nếu không so sánh thì sẽ liên tục cập nhật lại trạng thái mới của chính action cũ
        if new_action != self.action:
            self.action = new_action
            self.frame_idx = 0                                   # Thiết lập trạng thái ban đầu cho action mới
            self.update_timer_status = pygame.time.get_ticks()   # Set timer cho trạng thái 1 action

    def update_anim_frame(self):
        # Kiểm tra thỏa mãn thời gian chờ thì thay đổi trạng thái trong 1 action
        if pygame.time.get_ticks() - self.update_timer_status >= ANIM_COOLDOWN:
            self.update_timer_status = pygame.time.get_ticks()    # Cập nhật lại thời gian
            self.frame_idx += 1                                   # Chuyển trạng thái của hành động theo chỉ số của trạng thái đó
            # Kiểm tra nếu đã qua trạng thái cuối cùng trong 1 action
            if self.frame_idx >= len(self.anim_list[self.action]):
                # Mà đang trong action death thì giữ nguyên ở trạng thái cuối cùng thôi để Soldier nằm đó
                if self.action == 3:
                    self.frame_idx = len(self.anim_list[self.action]) - 1
                # Còn không thì trở về trạng thái đầu tiên của action đó
                else: self.frame_idx = 0
        self.image = self.anim_list[self.action][self.frame_idx]  # Cập nhật ảnh để vẽ lên màn hình

    def AI(self):
        # Nếu player và enemy cùng sống thì enemy mới hoạt động và thực hiện các hoạt động
        if self.alive and player_.alive:
            # Nếu enemy đang tuần tra thì sẽ kích hoạt idle theo random và không bắt player
            if not self.idling and randint(1,300) == 1:
                self.update_action(0)  # Cập nhật ảnh vẽ lên
                self.idling = True     # Kiểm soát trạng thái idle
                self.idling_cnt = 100  # Set timer cho trạng thái idle

            # Nếu bắt được player thì kích hoạt idle và đứng bắn còn không thì tuần tra tiếp
            if self.vision.colliderect(player_.rect):
                # Xét vị trí tương đối của enemy và player lấy hướng liên quan đến việc tạo đạn để không bị bắn ngược lại
                # Try tránh chia cho 0
                try:
                    self.direction = -(self.rect.x - player_.rect.x) / abs((self.rect.x - player_.rect.x))
                except Exception: pass
                # Lật ảnh khi player đứng trước enemy
                if(self.rect.x - player_.rect.x > 0): self.flip = True
                else: self.flip = False
                self.update_action(0)
                self.shoot()
            else:
                # Nếu enemy đang đi tuần thì tự động chạy và cập nhật hướng theo bộ đếm
                if not self.idling:
                    if self.direction == 1: ai_moving_right = True
                    else: ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)  # Cho enemy di chuyển
                    self.update_action(1)                       # Cập nhật action running
                    self.step_cnt += 1                          # Đếm số bước kiểm soát khu vực tuần tra
                    if self.step_cnt > TILE_SIZE-5:
                        self.direction *= -1                    # Dủ số bước thì quay đầu
                        self.step_cnt = 0                       # Tính số bước lại từ đầu
                    # Cập nhật tầm nhìn khi enemy di chuyển
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    # pygame.draw.rect(DISPLAYSURF, RED, self.vision)
                # Nếu đang idle thì giảm bộ đếm và kiểm tra hết thời gian thì set lại về running
                else:
                    self.idling_cnt -= 1
                    if self.idling_cnt <= 0:
                        self.idling = False
                        self.update_action(1)

        # Player di chuyển thì enemy vẫn phải di chuyển tương đối so với player dù còn sống hay không
        self.rect.x += SCREEN_SCROLL

    # update() tổng quát cho soldier
    def update(self):
        #pygame.draw.rect(DISPLAYSURF, RED, self.rect)
        # Không cập nhật action vì action enemy và player là khác nhau
        # Chỉ cập nhật những gì chung của player và enemy còn riêng thì cho vào game loop
        self.update_anim_frame()    # Cập nhật trạng thái trong 1 action
        self.check_death()          # Liên tục cập nhật trạng thái còn sống
        # Kiểm soát thời gian giữa 2 lần bắn
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        
    def draw(self):
        # self.flip kiểm soát việc lật sprite theo hướng của soldier
        DISPLAYSURF.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class World():
    def __init__(self):
        self.obstacle_lst = []      # List các vật thể được xét là bề mặt di chuyển - khối đất

    # Duyệt qua dữ liệu đã được nạp vào với mỗi tile
    def loading_data(self, data: list):
        # Lấy dữ liệu về chiều dài 1 level để xử lý khi player đến cuối map sẽ không cuộn nữa
        self.level_length = len(data[0])
        for y, row in enumerate(data):              # Lấy nguyên 1 hàng là 1 list kèm chỉ số hàng
            for x, tile in enumerate(row):          # Lấy dữ liệu các ô tilemap kèm chỉ số
                # Chỉ lấy dữ liệu của ô nào nằm trong dải chỉ số
                if tile >= 0:
                    img = img_tiles_lst[tile]       # Lấy hình ảnh ứng với chỉ số tương ứng
                    img_rect = img.get_rect()       # Xử lý va chạm
                    img_rect.x = x * TILE_SIZE      # Set vị trí tiles (topleft) theo các hàng và cột ứng với từng ô
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)     # Gói các thông tin của 1 tile lại để dễ xử lý và coi như 1 đối tượng
                    
                    if tile <= 8:                   # Gom các tile được xét va chạm lại - khối đất
                        self.obstacle_lst.append(tile_data)
                    elif tile == 9 or tile == 10 or tile == 22:
                        trap = Trap(img, x*TILE_SIZE, y*TILE_SIZE)
                        trap_group.add(trap)
                    elif (tile >= 11 and tile <= 14):
                        decor = Decoration(img, x*TILE_SIZE, y*TILE_SIZE)
                        decor_group.add(decor)
                    elif tile == 15:
                        player_= Soldier('player',x*TILE_SIZE, y*TILE_SIZE,1.65,5,20,10)
                        health_bar = HealthBar(0,0,100)
                    elif tile == 16:
                        enemy_1 = Soldier('enemy', x*TILE_SIZE, y*TILE_SIZE,1.65,3,10,0)
                        enemy_group.add(enemy_1)
                    elif tile == 17:
                        item_1 = ItemBox('Ammo', x*TILE_SIZE, y*TILE_SIZE)
                        item_box_group.add(item_1)
                    elif tile == 18:
                        item_1 = ItemBox('Grenade', x*TILE_SIZE, y*TILE_SIZE)
                        item_box_group.add(item_1)
                    elif tile == 19:
                        item_1 = ItemBox('Health', x*TILE_SIZE, y*TILE_SIZE)
                        item_box_group.add(item_1)
                    elif tile == 20:
                        # 1 đối tượng là cổng và 1 đối tượng là hố đen
                        img = pygame.transform .scale(img, (TILE_SIZE*4,TILE_SIZE*4))
                        gate = Gate(img, x*TILE_SIZE, y*TILE_SIZE)
                        exit = Exit(x*TILE_SIZE, y*TILE_SIZE, 0.1)
                        exit_group.add(exit)
                        exit_group.add(gate)
                    elif tile == 21:
                        torch = Torch(img, x*TILE_SIZE, y*TILE_SIZE)
                        decor_group.add(torch)
                    elif tile == 23:
                        # Chỉ có 1 key nên được xử lý riêng biệt và phải return
                        key = Key(img, x*TILE_SIZE, y*TILE_SIZE)
                    elif tile == 24:
                        img = pygame.transform.scale(img, (46,64))
                        princess = Decoration(img, x*TILE_SIZE, y*TILE_SIZE)
                        decor_group.add(princess)
        return player_, health_bar, key

    def draw(self):
        # Ở đây chỉ xử lý bề mặt di chuyển nên các object khác sẽ được xử lý riêng
        for tile in self.obstacle_lst:
            # Điều chỉnh hiển thị khi nhân vật di chuyển thì scene di chuyển theo hướng ngược lại
            tile[1][0] += SCREEN_SCROLL
            DISPLAYSURF.blit(tile[0],tile[1]) # Danh sách các tuple chứa thông tin 1 tile



class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        # Vẽ ở trung điểm cạnh đáy trên để đặt vào giữa ô tạo sự cân đối
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())
    # Khi plyer di chuyển thì cập nhật vị trí tương đối
    def update(self):
        self.rect.x += SCREEN_SCROLL



class Torch(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.images = []                # Nạp các trạng thai của đuốc
        for i in range(len(os.listdir(os.path.join('Assets','Image','torch')))):
            img = pygame.image.load(os.path.join('Assets','Image','torch',f'{i}.png')).convert_alpha()
            img = pygame.transform.scale(img, (TILE_SIZE*2, TILE_SIZE*2))
            self.images.append(img)
        self.frame_idx = 0
        self.image = self.images[self.frame_idx]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)
        self.counter = 0                # Bộ đếm cho phép chuyển trạng thái

    def update(self):
        self.rect.x += SCREEN_SCROLL
        if self.counter < 3: self.counter += 1
        else:
            self.frame_idx = (self.frame_idx + 1) % len(os.listdir(os.path.join('Assets','Image','torch')))
            self.counter = 0
        self.image = self.images[self.frame_idx]



class Trap(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        # Vẽ ở trung điểm cạnh đáy để đặt vào giữa ô tạo sự cân đối
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())
    # Khi plyer di chuyển thì cập nhật vị trí tương đối
    def update(self):
        self.rect.x += SCREEN_SCROLL



class Gate(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        # Vẽ ở trung điểm cạnh đáy để đặt vào giữa ô tạo sự cân đối
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE + 33)
    # Khi plyer di chuyển thì cập nhật vị trí tương đối
    def update(self):
        self.rect.x += SCREEN_SCROLL



class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        super().__init__()
        self.images = []
        for i in range(len(os.listdir(os.path.join('Assets','Image','exit')))):
            img = pygame.image.load(os.path.join('Assets','Image','exit',f'{i}.png')).convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale*1.3)))
            self.images.append(img)
        self.frame_idx = 0
        self.image = self.images[self.frame_idx]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)
        self.counter = 0                # Bộ đếm cho phép chuyển trạng thái

    def update(self):
        self.rect.x += SCREEN_SCROLL
        if self.counter < 3:
            self.counter += 1
        else: 
            self.frame_idx = (self.frame_idx + 1) % len(os.listdir(os.path.join('Assets','Image','exit')))
            self.counter = 0
        self.image = self.images[self.frame_idx]



class ItemBox(pygame.sprite.Sprite):
    def __init__(self, type_ : str,x,y) -> None:
        super().__init__()
        self.item_type = type_
        self.image = item_boxes_lst[self.item_type]     # Lấy ảnh theo key của dict đã tạo trước đó
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())
    def update(self):
        # Khi plyer di chuyển thì cập nhật vị trí tương đối
        self.rect.x += SCREEN_SCROLL
        # Kiểm tra va chạm với player thì tăng chỉ số
        if pygame.sprite.collide_rect(self, player_):
            if self.item_type == 'Health':
                player_.health += 25
                if player_.health > player_.max_health: player_.health = player_.max_health
            elif self.item_type == 'Ammo':
                if player_.ammo <= 10: player_.ammo += 10
                else: player_.ammo = 20
            elif self.item_type == 'Grenade':
                if player_.grenades <= 7: player_.grenades += 3
                else: player_.grenades = 10
            self.kill()



class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir):
        super().__init__()
        self.image = bullet_image               # Lấy sprite
        self.rect = self.image.get_rect()       # Tạo khung xử lý vật lý
        self.rect.center = (x,y)                # Set vị trí
        self.direction = dir                    # Set hướng theo soldier

    def update(self):
        # Cập nhật tọa độ theo hướng đi của soldier
        self.rect.x += speed_of_bullet * self.direction
        # Nếu ra khỏi khung nhìn thì hủy đối tượng bullet đó đi
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        # Nếu soldier va chạm với bullet và còn sống thì sẽ gây sát thương rồi hủy đạn đó đi
        if pygame.sprite.spritecollide(player_, bullet_group, False):
            if player_.alive:
                player_.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()
        # Không cho đi qua vật cản, bắn xuyên tường
        for tile in world.obstacle_lst:
            if tile[1].colliderect(self.rect):
                self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, dir):
        super().__init__()
        self.timer = 100                        # Set thời gian đợi nổ tính từ lúc đối tượng được khởi tạo
        self.vel_y = -11                        # Set vận tốc rơi ban đầu
        self.vel_x = 9                          # Set vận tốc rơi theo chiều ngang
        self.image = grenade_image              # Lấy sprite
        self.rect = self.image.get_rect()       # Tạo khung xử lý vật lý
        self.rect.center = (x,y)                # Set vị trí
        self.direction = dir                    # Set hướng theo player
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.check_on_ground = False

    def update(self):

        dx = dy = 0
        # Giới hạn vận tốc rơi tự do là 10
        if self.vel_y < 10:
            self.vel_y += GRAVITY

        # Nếu không ở trên mặt đất thì mới cập nhật offset
        if not self.check_on_ground:
            dx = self.direction * self.vel_x
            dy = self.vel_y
        
        for tile in world.obstacle_lst:
            # Kiểm tra va chạm với vật chắn trước hoặc sau thì ném ngược lại và cập nhật lại độ dịch chuyển trên trục x
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1                  # Đổi chiều lựu đạn bay
                dx = self.direction * self.vel_x      
            # Kiểm tra va chạm với vật cản trên hoặc dưới thì rơi xuống và cập nhật lại độ dịch chuyển trên trục y
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.vel_x = 0          # Va chạm và rơi xuống ngay lập tức không cho di chuyển thêm theo trục x nữa
                if self.vel_y < 0:
                    self.vel_y = 0  # Set về 0 để các lần cập nhật sau sẽ là rơi xuống
                    dy = tile[1].bottom - self.rect.top
                # Nếu đang rơi xuống thì không cần cập nhật
                # Check luôn trường hợp va chạm với mặt đất thì giữ nguyên vị trí mà không di chuyển tiếp xuống
                elif not self.check_on_ground:
                    # Không cần cập nhật lại vận tốc rơi tự do
                    dy = tile[1].top - self.rect.bottom
                    self.check_on_ground = True

        self.rect.x += dx + SCREEN_SCROLL
        self.rect.y += dy

        '''
            Kích hoạt bộ đếm thời gian nổ để hủy grenade và tạo explosiom. Lựu đạn nổ gây dam với soldier xung quanh
            gây sát thương theo phạm vi bán kính (TILE)
        '''
        self.timer -= 1
        if self.timer == 0:
            self.kill()
            grenade_fx.play()
            explosion_instance = Explosion(self.rect.x, self.rect.y, 1.5)
            explosion_group.add(explosion_instance)
            if abs(self.rect.centerx - player_.rect.centerx) < TILE_SIZE and abs(self.rect.centery - player_.rect.centery) < TILE_SIZE:
                player_.health -= 50
            elif abs(self.rect.centerx - player_.rect.centerx) < TILE_SIZE*2 and abs(self.rect.centery - player_.rect.centery) < TILE_SIZE*2:
                player_.health -= 30
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE and abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE:
                    enemy.health -= 50
                elif abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE*2 and abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE*2:
                    enemy.health -= 30



# Vì các lựu đạn được xử lý riêng lẻ nên việc nổ cũng được xử lý riêng
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        super().__init__()
        self.images = []
        for i in range(len(os.listdir(os.path.join('Assets','Image','explosion')))):
            img = pygame.image.load(os.path.join('Assets','Image','explosion',f'exp{i}.png')).convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
            self.images.append(img)
        self.frame_idx = 0
        self.image = self.images[self.frame_idx]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.counter = 0                                # Quản lý các trạng thái của quá trình phát nổ

    # Nổ 1 lần nên dùng timer cụ thể
    # Có 4 khoảng thời gian nên sẽ dùng chia lấy nguyên tới khi gặp 20 thì sẽ hủy đối tượng
    def update(self):
        self.rect.x += SCREEN_SCROLL
        if self.counter < 20:
            self.counter += 1
            self.frame_idx = self.counter // EXPLOSION_COOLDOWN
            self.image = self.images[self.frame_idx]
        else: self.kill()


class HealthBar():
    def __init__(self, x, y, health):
        self.x = x
        self.y = y
        self.health = health

    def draw(self, health):
        self.health = health
        DISPLAYSURF.blit(bg_health_bar_img, (self.x, self.y))
        DISPLAYSURF.blit(rect_char_img_1, (self.x + 10, self.y + 10))
        DISPLAYSURF.blit(avt_img, (self.x + 15, self.y + 20))
        DISPLAYSURF.blit(health_bar_1_img, (self.x + 70, self.y + 15))
        DISPLAYSURF.blit(health_bar_2_img_current, (self.x + 73, self.y + 17))
        DISPLAYSURF.blit(bullet_bar_img, (self.x + 70, self.y + 30))
        draw_text(f": {player_.ammo}/{player_.start_ammo}", font_2, TEXT_COLOR, self.x + 70 + bullet_bar_img.get_width(), self.y + 35)
        DISPLAYSURF.blit(grenade_image, (self.x + 185,self.y + 38))
        draw_text(f": {player_.grenades}/{player_.start_grenades}", font_2, TEXT_COLOR, self.x + 190 + grenade_image.get_width(), self.y + 35)



class Screen_fade():
    def __init__(self,direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_cnt = 0

    def fade(self):
        fade_completed = False
        self.fade_cnt += self.speed

        if self.direction == 1:   # Phủ toàn màn hình
            pygame.draw.rect(DISPLAYSURF, self.color, (0 - self.fade_cnt, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT)) # trái 
            pygame.draw.rect(DISPLAYSURF, self.color, (SCREEN_WIDTH // 2 + self.fade_cnt, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT)) # phải
            pygame.draw.rect(DISPLAYSURF, self.color, (0, 0 - self.fade_cnt, SCREEN_WIDTH, SCREEN_HEIGHT // 2)) # lên
            pygame.draw.rect(DISPLAYSURF, self.color, (0, SCREEN_HEIGHT // 2 +self.fade_cnt, SCREEN_WIDTH, SCREEN_HEIGHT // 2)) # xuống

        if self.direction == 2:    # Màn hình đi xuống - đi xuống toàn bộ 
            pygame.draw.rect(DISPLAYSURF, self.color, (0,0,SCREEN_WIDTH, self.fade_cnt))

        if self.fade_cnt >= SCREEN_WIDTH:
            fade_completed = True
        return fade_completed
    


class Key(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        # Vẽ ở trung điểm cạnh đáy trên để đặt vào giữa ô tạo sự cân đối
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())
    # Khi plyer di chuyển thì cập nhật vị trí tương đối
    def update(self):
        self.rect.x += SCREEN_SCROLL


    
class Taking_her_home(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = []
        for i in range(len(os.listdir(os.path.join('Assets','Image','taking_her_home')))):
            img = pygame.image.load(os.path.join('Assets','Image','taking_her_home',f'{i}.png')).convert_alpha()
            img = pygame.transform.scale(img, (SCREEN_WIDTH, img.get_height()))
            self.images.append(img)
        self.frame_idx = 0
        self.image = self.images[self.frame_idx]
        self.counter = 0

    def update(self):
        if self.counter < 3: self.counter += 1
        else:
            self.frame_idx = (self.frame_idx + 1) % len(os.listdir(os.path.join('Assets','Image','torch')))
            self.counter = 0
        self.image = self.images[self.frame_idx]
        DISPLAYSURF.fill(BG_COLOR)
        DISPLAYSURF.blit(self.image,(0, 100))



# ====================================================== GAME METHODS ====================================================== #

def draw_bg():

    DISPLAYSURF.fill((144,201,120))
    wid = sky_img.get_width()
    # Vẽ nhiều background liên tiếp tạo hiệu ứng vô cực, layer ở xa di chuyển chậm hơn so với player
    for x in range(20):
        DISPLAYSURF.blit(sky_img,((x*wid) - BG_SCROLL * 0.1,0))
        DISPLAYSURF.blit(cloud_img,((x*wid) - BG_SCROLL * 0.2,SCREEN_HEIGHT - cloud_img.get_height() - 300))
        DISPLAYSURF.blit(mountain1_img,((x*wid) - BG_SCROLL * 0.3,SCREEN_HEIGHT - mountain1_img.get_height() - 50 ))
        DISPLAYSURF.blit(mountain2_img,((x*wid) - BG_SCROLL * 0.4,SCREEN_HEIGHT - mountain2_img.get_height()))

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    DISPLAYSURF.blit(img, (x,y))

def draw_tutorial():

    DISPLAYSURF.blit(bg_tutorial,(50,100))
    DISPLAYSURF.blit(char_sample_img,(90,170))
    draw_text("Find the keys then", font_1, TEXT_COLOR, 100 + char_sample_img.get_width(), 210)
    draw_text("Rescue the princess !", font_1, TEXT_COLOR, 100 + char_sample_img.get_width(), 240)
    

    draw_text(f'Press/Hold ', font_1, TEXT_COLOR, 90, SCREEN_HEIGHT - 300)
    DISPLAYSURF.blit(arrow_button_img, (220 , SCREEN_HEIGHT - 300))
    draw_text(f' to move', font_1, TEXT_COLOR, 220 + arrow_button_img.get_width(), SCREEN_HEIGHT - 300)
    
    draw_text(f'Press/Hold ', font_1, TEXT_COLOR, 90, SCREEN_HEIGHT - 250)
    DISPLAYSURF.blit(space_button_img, (220 , SCREEN_HEIGHT - 240))
    draw_text(f' to shoot', font_1, TEXT_COLOR, 220 + space_button_img.get_width(), SCREEN_HEIGHT - 250)

    draw_text(f'Press/Hold ', font_1, TEXT_COLOR, 90, SCREEN_HEIGHT - 200)
    DISPLAYSURF.blit(n_button_img, (220 , SCREEN_HEIGHT - 190))
    draw_text(f' to throw grenade', font_1, TEXT_COLOR, 220 + n_button_img.get_width(), SCREEN_HEIGHT - 200)

    draw_text(f'Press ', font_1, TEXT_COLOR, 90, SCREEN_HEIGHT - 150)
    DISPLAYSURF.blit(esc_button_img, (160 , SCREEN_HEIGHT - 140))
    draw_text(f' to quit game', font_1, TEXT_COLOR, 165 + esc_button_img.get_width(), SCREEN_HEIGHT - 150)

    
def taking_her_home_sound():
    pygame.mixer.music.load(os.path.join('Assets','Audio','HARLEY_DAVIDSON.mp3'))
    pygame.mixer.music.play(-1)


def reset_level():

    bullet_group.empty()             
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decor_group.empty()
    trap_group.empty()
    exit_group.empty()
    enemy_group.empty()

    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data



# ====================================================== INITIALIZATION ====================================================== #

start_button = Button(SCREEN_WIDTH * 3 // 4 - start_btn_image.get_width() // 2, SCREEN_HEIGHT // 2 - 100,start_btn_image, 1)
exit_button_1 = Button(SCREEN_WIDTH * 3 // 4 - exit_btn_image.get_width() // 2, SCREEN_HEIGHT // 2 + 70,exit_btn_image, 1)
exit_button_2 = Button(SCREEN_WIDTH // 2 - exit_btn_image.get_width() // 2, SCREEN_HEIGHT // 2 + 100,exit_btn_image, 1)
restart_button = Button(SCREEN_WIDTH // 2 - restart_btn_image.get_width(), SCREEN_HEIGHT // 2 - 50,restart_btn_image, 2)
death_fade = Screen_fade(2, BG_COLOR, 5)
intro_fade = Screen_fade(1, BG_COLOR, 5)

bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decor_group = pygame.sprite.Group()
trap_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
vid = Taking_her_home()

# Tạo danh sách 2 chiều lưu tile map - Level Editor (-1 : Nothing)
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)

# Đọc vào dữ liệu mỗi level ứng với các loại tile được sử dụng ở mỗi ô
with open(os.path.join('Assets','Tiles_map',f'level{level}_data.csv'), newline='') as csv_file:
    reader = csv.reader(csv_file, delimiter=',') # Trả về 1 list các list
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

world = World()
player_, health_bar, key = world.loading_data(world_data)



# ====================================================== GAME LOOPS ====================================================== #

running = True
while running:

    keys_pressed = pygame.key.get_pressed()

    if keys_pressed[pygame.K_a]:
        moving_left = True
    if keys_pressed[pygame.K_d]:
        moving_right = True
    # Vì kiểm tra quá nhanh nên trong 1 lần nhấn phím sẽ ghi nhận được nhiều lần jump gây ra nhảy nhiều lần
    # Khi vừa nhảy lên thì chưa kích hoạt in_air nên isJumping vẫn kịp truyền cho hàm move ngay trong vòng lặp hiện tại để kích hoạt in_air
    if keys_pressed[pygame.K_w] and player_.alive:
        player_.isJumping = True
    if keys_pressed[pygame.K_SPACE]:
        isShooting = True
    if keys_pressed[pygame.K_n]:
        is_throwing_grenade = True
    if keys_pressed[pygame.K_ESCAPE]:
        running = False
        

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_w:
                jmp_fx.play()
                player_.isJumping = False
            if event.key == pygame.K_n:
                is_throwing_grenade = False
                grenade_thrown = False
            if event.key == pygame.K_SPACE:
                isShooting = False


    
    # Bắt đầu khối lệnh khi nhấn START
    if START_GAME:

        # Kiểm soát nhiệm vụ nhặt chìa khóa và qua màn
        if player_.rect.colliderect(key.rect):
            player_.key_picked = True

        # Vẽ background làm layer đầu tiên
        draw_bg()
        world.draw()

        health_bar.draw(player_.health)
        # Thanh máu được cập nhật theo thời gian thực
        health_bar_2_img_current = pygame.transform.scale(health_bar_2_img_original, ((health_bar_2_img_original.get_width()*player_.health) // 100, health_bar_2_img.get_height()))
        
        # Cập nhật trạng thái các nhóm đối tươngj
        bullet_group.update()             
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        trap_group.update()
        exit_group.update()
        decor_group.update()
        if(player_.key_picked == False): key.update()       # Nếu chưa nhặt được chìa khóa thì vẫn cập nhật vị trí key

        bullet_group.draw(DISPLAYSURF)
        grenade_group.draw(DISPLAYSURF)
        explosion_group.draw(DISPLAYSURF)
        item_box_group.draw(DISPLAYSURF)
        
        trap_group.draw(DISPLAYSURF)
        exit_group.draw(DISPLAYSURF)
        decor_group.draw(DISPLAYSURF)
        if(player_.key_picked == False): DISPLAYSURF.blit(key.image, (key.rect.midtop)) # Vẽ key lên màn hình

        player_.update()
        player_.draw()

        for enemy in enemy_group:
            enemy.AI()
            enemy.update()
            enemy.draw()

        # Dựa vào biến kiểm soát level để chạy video
        if VIDEO_PLAYED: vid.update()

        # Kiểm soát việc chạy hiệu ứng chuyển màn, chạy xong sẽ reset các chỉ số
        if START_INTRO:
            if intro_fade.fade():
                START_INTRO = False
                intro_fade.fade_cnt = 0

        if player_.alive:
            if isShooting:
                player_.shoot()
            # Nếu vừa ném và đã nhả phím mới cho ném tiếp. Xử lý theo 1 group
            if is_throwing_grenade and not grenade_thrown and player_.grenades > 0:
                grenade_instance = Grenade(player_.rect.centerx + (0.5*player_.rect.size[0]*player_.direction),player_.rect.top, player_.direction)
                grenade_group.add(grenade_instance)
                grenade_thrown = True
                player_.grenades -= 1
            # Nếu đang lơ lửng thì cập nhật action
            if player_.in_air:
                player_.update_action(2)
            elif moving_left or moving_right:
                player_.update_action(1)
            else:
                player_.update_action(0)

            # Trả về các biến được xử lý trong hàm coi như cập nhật
            SCREEN_SCROLL, level_completed = player_.move(moving_left, moving_right)

            # Cập nhật độ dịch background so với gốc tọa độ ban đầu theo độ dịch player
            BG_SCROLL -= SCREEN_SCROLL

            # Nếu đã hoàn thành level thì chạy hiệu ứng chuyển màn và nạp dữ liệu
            if level_completed:
                player_.key_picked = False
                START_INTRO = True
                level += 1
                BG_SCROLL = 0 # Set background về lại vị trí ban đầu
                world_data = reset_level()
                # Kiểm tra còn vòng chơi mới cho nạp dữ liệu nếu không sẽ bị crash
                if level <= MAX_LEVELS:
                    with open(os.path.join('Assets','Tiles_map',f'level{level}_data.csv'), newline='') as csv_file:
                        reader = csv.reader(csv_file, delimiter=',') # Trả về 1 list các list
                        # Duyệt list không biết idx nên cần sủ dụng enumerate - trả về idx - val để set cho từng vị trí data_world
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()    # tạo 1 đối tượng tile map
                    player_, health_bar, key = world.loading_data(world_data)
                # Nêu đã hết màn thì cho phép chạy video phần thưởng taking her home
                else:
                    VIDEO_PLAYED = True
                    taking_her_home_sound()

        # Xử lý khi game over
        else:
            # Khi game over thì dx của player vẫn còn giá trị != 0 nếu restart sẽ gây lỗi
            SCREEN_SCROLL = 0
            # Khi màn hình hiện hết thì nút restart mới hiện lên
            if death_fade.fade():
                DISPLAYSURF.blit(game_over_img,(SCREEN_WIDTH//2-game_over_img.get_width()//2,50))
                # Nếu chọn nút restart
                if restart_button.draw(DISPLAYSURF):
                    player_.key_picked = False              # Reset trạng thái nhặt key
                    player_.GAME_OVER_FX_PLAYED = False     # Cập nhật trạng thái chạy nhạc gameover cho lần tiếp theo
                    death_fade.fade_cnt = 0                 # Reset lại chỉ số cho lần sau
                    START_INTRO = True                      # Lại cho chạy hiệu ứng chuyển màn khi restart
                    BG_SCROLL = 0                           # Set background về lại vị trí ban đầu tránh lỗi
                    world_data = reset_level()              # Nạp lại dữ liệu level đó
                    with open(os.path.join('Assets','Tiles_map',f'level{level}_data.csv'), newline='') as csv_file:
                        reader = csv.reader(csv_file, delimiter=',') # Trả về 1 list các list
                        # Duyệt list không biết idx nên cần sủ dụng enumerate - trả về idx - val để set cho từng vị trí data_world
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()    # tạo 1 đối tượng tile map
                    player_, health_bar, key = world.loading_data(world_data)
                # Nếu chọn exit thì thoát game
                elif exit_button_2.draw(DISPLAYSURF):
                    running = False

    # Nếu chưa start thì vẽ Menu Start
    else:
        '''
        Hiệu ứng infinity background: Vẽ 2 bộ background nối tiếp nhau cho di chuyển theo OFFSET_BG_MENU nhưng không cho vượt quá chiều dài
        của background.
        '''
        wid = bg_menu_img.get_width()
        for x in range(2):
            DISPLAYSURF.blit(bg_menu_img,((x*wid) - OFFSET_BG_MENU,0))
        OFFSET_BG_MENU = (OFFSET_BG_MENU + 0.5) % wid

        # Vẽ tutorial
        draw_tutorial()

        if start_button.draw(DISPLAYSURF):
            START_GAME = True
            START_INTRO = True

        elif exit_button_1.draw(DISPLAYSURF):
            running = False

    FPS.tick(60)

    pygame.display.update()

pygame.quit()