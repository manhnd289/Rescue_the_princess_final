import pygame 

class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, surface):
		trigger = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		# Kiểm tra nếu rect của button va chạm với vị trí của chuột không 
		if self.rect.collidepoint(pos):
			# Chuột trái giờ mới được nhấn
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				trigger = True           # Kích hoạt nút đó
				self.clicked = True		 # Đánh dấu là đã được nhấp vào rồi
		# Kiểm tra nếu nhả chuột thì cập nhật trạng thái được nhấn
		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		# Vẽ nút lên
		surface.blit(self.image, (self.rect.x, self.rect.y))

		# Trả về trạng thái kích hoạt của nút đó
		return trigger