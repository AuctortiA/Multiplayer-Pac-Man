__author__ = 'Will Evans'
import pygame as pg
import os.path
import sprites


class Word:
    def __init__(self, content, pos, colour, font_size, win_scale, italic=False, bold=False, centre=False, left=False):
        """
        Class used to put a word on the screen.
        :param content: String: content of the word.
        :param pos: (x, y) position of word.
        :param colour: (r, g, b) value of colour.
        :param font_size: Font size.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param italic: Boolean: italics or not.
        :param bold: Boolean: bold or not.
        :param centre: Boolean: centre or not.
        :param left: Boolean: align left or not.
        """

        self.content = content

        x, y = pos
        self.x = x * win_scale
        self.y = y * win_scale

        self.colour = colour
        self.centre = centre
        self.left = left
        self.__letters = []

        font_path = os.path.join('resources', 'fonts', 'ARCADECLASSIC.TTF')
        self._font = pg.font.Font(font_path, font_size * win_scale)
        self._font.set_italic(italic)
        self._font.set_bold(bold)

        if self.content is not None:
            self.render()

    def display(self, win):
        """
        Blits the rendered font to the screen as per the rect.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        if self.content is not None:
            win.blit(self._rendered_text, self._text_rect)

    def render(self):
        """
        Renders font. Takes the content and colour and converts this into a font object. Then a rect object is created
        based on the position and alignment instructions.
        :return: None
        """

        self._rendered_text = self._font.render(self.content, True, self.colour)

        if self.centre:
            self._text_rect = self._rendered_text.get_rect(center=(self.x, self.y))
        elif self.left:
            self._text_rect = self._rendered_text.get_rect(midleft=(self.x, self.y))
        else:
            self._text_rect = self._rendered_text.get_rect(midright=(self.x, self.y))


class LiveWord:
    def __init__(self, content, y, font_size, win_scale, highlight_colour=(255, 255, 255)):
        """
        Live words have the ability to highlight when selected by the user. Separate to word class as live
        words must be rendered letter by letter so that when the highlighted layer is shown, it correctly covers each
        individual letter.
        :param content: String: content of the word.
        :param y: y coordinate of word (do not require x as they are automatically centred).
        :param font_size: Integer: Font size
        :param win_scale: Integer: Window Scale (How large the window is - must be multiplied by all size related
        variables).
        :param highlight_colour: (r, g, b): default is set to white but can be any colour.
        """

        self.program = content
        self.content = list(content)
        self.__letters = []
        self.__react = False
        self.__letter_spacing = font_size * 7/12

        for num, letter in enumerate(content):
            x = 173 + ((- len(content) / 2) + num) * self.__letter_spacing
            self.__letters.append(LiveLetter(letter, x, y, font_size, win_scale, highlight_colour))

    def react(self):
        self.__react = True

    def display(self, win):
        """
        Displays each letter in the word, sets react to False so that if the mouse stops colliding with the word,
        then the word will stop displaying as highlighted.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :return: None.
        """

        for letter in self.__letters:
            letter.display(self.__react, win)
        self.__react = False

    def check_mouse(self, x, y):
        """
        Returns true if the x, y coordinates supplied are colliding with any of the letters' rects.
        :param x: x coord of mouse.
        :type x: Integer/
        :param y: y coord of mouse.
        :type y: Integer/
        :return: Boolean: True if mouse is colliding with letters, false if mouse is not.
        """

        for letter in self.__letters:
            if letter.check_mouse(x, y):
                return True
        return False

    def check_click(self, x, y):
        """
        Checks each letter to see if any of them have been clicked by the mouse.
        :param x: x coord of mouse that has been clicked.
        :type x: Integer.
        :param y: y coord of mouse that has been clicked.
        :type y: Integer.
        :return: Returns true if any of the letters have been clicked on else false.
        """

        for letter in self.__letters:
            if letter.check_mouse(x, y):
                return True

    def get_program(self):
        return self.program


class LiveLetter:
    def __init__(self, letter, x, y, font_size, win_scale, highlight_colour):
        """
        Live letters are used by the live words class. They control one letter each.
        :param letter: The letter that will be rendered.
        :type letter: String.
        :param x: x coord of letter position.
        :type x: Integer.
        :param y: y coord of letter position.
        :type y: Integer.
        :param font_size: Font size.
        :type font_size: Integer.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param highlight_colour: (r, g, b) colour of the highlighted part of the letter.
        :type highlight_colour: Tuple.
        """

        self.__font_size = font_size * win_scale
        self.x = x * win_scale
        self.y = y * win_scale

        font_path = os.path.join('resources', 'fonts', 'ARCADECLASSIC.TTF')

        self.__font = pg.font.Font(font_path, self.__font_size)
        self.__rendered_text = self.__font.render(letter, True, (255, 255, 30))
        self.__text_rect = self.__rendered_text.get_rect(center=(self.x, self.y))

        self.__outline1 = pg.font.Font(font_path, int(self.__font_size * 54 / 50))
        self.__rendered_outline1 = self.__outline1.render(letter, True, pg.Color('black'))
        self.__outline1_rect = self.__rendered_outline1.get_rect(center=(self.x, self.y))

        self.__outline = pg.font.Font(font_path, int(self.__font_size * 62 / 50))
        self.__rendered_outline = self.__outline.render(letter, True, highlight_colour)
        self.__outline_rect = self.__rendered_outline.get_rect(center=(self.x, self.y))

    def display(self, react, win):
        """
        Blits the letter object to the screen. If react is True, then a black outline and another outline will be
        blitted behind to highlight the letter.
        :param react: Whether or not the letter will be highlighted or not.
        :type react: Boolean.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :return: None.
        """

        if react:
            win.blit(self.__rendered_outline, self.__outline_rect)
            win.blit(self.__rendered_outline1, self.__outline1_rect)
            win.blit(self.__rendered_text, self.__text_rect)
        else:
            win.blit(self.__rendered_text, self.__text_rect)

    def check_mouse(self, x, y):
        """
        Checks whether the x, y co-ords are colliding with the letter.
        :param x: x coord of mouse.
        :type x: Integer.
        :param y: y coord of mouse.
        :type y: Integer.
        :return: True if the x, y coordinates are colliding with the text rect.
        """

        return self.__text_rect.collidepoint(x, y)


class ScrollingWord:
    def __init__(self, content, pos, colour, font_size, win_scale, frame_cap=1):
        """
        Scrolling words uses the word class (constantly re renders it) to give the appearance of scrolling / revealing
        text.
        :param content: String: content of the word.
        :param pos: (x, y) position of word.
        :param colour: (r, g, b) value of colour.
        :param font_size: Font size.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        """

        self.content = content
        self.content_displayed = ''
        self.characters_displayed_num = 0
        self.finished = False

        self.rendered_font = Word(self.content_displayed, pos, colour, font_size, win_scale, False, False, False, True)

        self.frame_count = 0
        self.frame_cap = frame_cap

    def update(self, events):
        self.frame_count += 1
        if self.frame_count == self.frame_cap:
            self.frame_count = 0

            if self.content == self.content_displayed:
                self.finished = True
            else:
                self.content_displayed += self.content[self.characters_displayed_num]
                self.characters_displayed_num += 1
                self.rendered_font.content = self.content_displayed
                self.rendered_font.render()

    def display(self, win):
        self.rendered_font.display(win)

    def render_all(self):
        self.content_displayed = self.content
        self.characters_displayed_num = len(self.content)
        self.rendered_font.content = self.content_displayed
        self.rendered_font.render()


class TutorialTextBox:
    def __init__(self, content, colour, win_scale, add_mspacman=False):
        """
        Uses the scrolling word, and box class to display scrolling text that can go over onto many lines
        all in a neat and tidy box.
        :param content: The boxes text content.
        :param colour: The colour of the text in the box.
        :param add_mspacman: Decides whether the text box should also include a sprite of mspacman.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        """

        # Essential
        self.win_scale = win_scale
        self.paused = False
        self.finished = False

        self.add_mspacman = add_mspacman

        # Words
        self.content = [f'{word}  ' for word in content.split(' ')]
        self.content_remaining = self.content
        self.colour = colour
        self.win_scale = win_scale
        self.font_size = 20
        self.x_prespacing = 15 if not self.add_mspacman else 80
        self.max_length = 340 - self.x_prespacing

        # This is a lovely trick to calculate how long the text will be (so that we know when to use a newline). By
        # rendering the font here we can use this object to get the width.
        font_path = os.path.join('resources', 'fonts', 'ARCADECLASSIC.TTF')
        self.font = pg.font.Font(font_path, self.font_size)

        self.boxes = []

        while len(self.content_remaining) > 0:
            self.render_box()

        self.active_box_index = 0
        self.active_box = self.boxes[self.active_box_index]

        # Box
        self.box = Box((7, 360), (321, 60), (230, 230, 230), 2, win_scale)

        # Transparent Win
        self.transparent_win = pg.Surface((321 * win_scale, 60 * win_scale))
        self.transparent_win.set_alpha(225)
        self.transparent_win.fill((161, 161, 161))

        mspacman_skin_paths = [os.path.join('resources', 'sprites', 'ms.pac-man', f'{num}.png') for num in (0, 1)]
        mspacman_skins = [pg.transform.scale(pg.image.load(path), ((56 * win_scale), (56 * win_scale)))
                          for path in mspacman_skin_paths]
        mspacman_rect = mspacman_skins[0].get_rect(center=(40 * win_scale, 370 * win_scale))
        self.mspacman = sprites.StaticSprite(mspacman_skins, mspacman_rect)

    def update(self, events):

        space_pressed = False

        # Words
        if len(self.boxes) > 0:
            for line in self.active_box:
                if line.finished:
                    continue
                line.update(events)
                break

        self.paused = all([line.finished for line in self.active_box])

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    space_pressed = True

        if self.paused and not self.finished and space_pressed:
            self.active_box_index += 1
            if self.active_box_index == len(self.boxes):
                self.finished = True
            else:
                self.active_box = self.boxes[self.active_box_index]
        elif space_pressed:
            for line in self.active_box:
                line.render_all()

        if not self.paused and self.add_mspacman:
            self.mspacman.update(events)

    def display(self, win):

        # Transparent Win
        win.blit(self.transparent_win, (7 * self.win_scale, 360 * self.win_scale))

        # Words

        for line in self.active_box:
            line.display(win)

        # Box
        self.box.display(win)

        # MsPacMan
        if self.add_mspacman:
            self.mspacman.display(win)

    def render_box(self):
        content_buffer = ''
        line_num = 0
        lines = []

        for word in self.content_remaining:
            content_buffer += word
            self.content_remaining = self.content_remaining[1:]

            if len(self.content_remaining) == 0:
                lines.append(
                    ScrollingWord(content_buffer, (self.x_prespacing, 375 + 15 * line_num), self.colour, self.font_size,
                                  self.win_scale, 2))

                self.boxes.append(lines)
                break

            current_length = self.font.size(content_buffer)[0] + self.font.size(self.content_remaining[0])[0]
            ellipsis_exit = word.replace(' ', '')[:-4:-1] == '...'
            if current_length >= self.max_length or ellipsis_exit:
                lines.append(
                    ScrollingWord(content_buffer,
                                  (self.x_prespacing,
                                   375 + 15 * line_num),
                                  self.colour,
                                  self.font_size,
                                  self.win_scale,
                                  2)
                        )

                line_num += 1
                content_buffer = ''

            if line_num == 3 or ellipsis_exit:
                self.boxes.append(lines)
                break


class Box:
    def __init__(self, pos, dimensions, colour, width, win_scale, centre=False):
        """
        Boxes are simply rectangles. They are capable of changing colour when a colour when a mouse is colliding with it
        however, this requires external support form code at the moment. Boxes are often aggregated. For example, they are
        used in input boxes etc.
        :param pos: (x, y) Contains the x and y coordinates of the box.
        :type pos: Tuple.
        :param dimensions: (w, h) Contains width and height of the box.
        :type dimensions: Tuple.
        :param colour: (r, g, b) colour of box.
        :type colour: Tuple.
        :param width: Width of the box line.
        :type width: Integer.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type: Integer.
        :param centre: If True the x, y values will become the centre of the box. Otherwise the top left is used by
        default.
        :type centre: Boolean.
        """

        x, y = pos
        w, h = dimensions

        if centre:
            self.rect = pg.Rect((x-1/2*w) * win_scale, (y-1/2*h) * win_scale, w * win_scale, h * win_scale)
        else:
            self.rect = pg.Rect(x * win_scale, y * win_scale, w * win_scale, h * win_scale)
        self.colour = colour
        self.width = width * win_scale

    def display(self, win):
        """
        Blits the box to the screen.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :return: None.
        """     

        pg.draw.rect(win, self.colour, self.rect, self.width)

    def check_mouse(self, x, y):
        return self.rect.collidepoint(x, y)


class InputBox:
    def __init__(self, x, y, w, h, font_size, win_scale, name='', interactive=True, centre=False, private=False,
                 max_length=14):
        """
        Input boxes use a box object and a word object (or will do). They are used to allow the user to allow the input
        of words from the user.
        :param x: x coord of box.
        :type x: Integer.
        :param y: y coord of box.
        :type: y: Integer.
        :param w: Width of box in pixels.
        :type w: Integer.
        :param h: Height of box in pixels.
        :type: h: Integer.
        :param font_size: Font size.
        :type font_size: Integer.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param name: This is the string that will display if the text box is empty at any time.
        :type name: String.
        :param interactive: Whether or not the box should respond to any user input. If false the input box becomes a
        text box.
        :type interactive: Boolean.
        :param centre: If True the x, y values will become the centre of the box. Otherwise the top left is used by
        default.
        :type centre: Boolean.
        :param private: If True the text in the box will be asterisks. This is useful for password input boxes.
        :type private: Boolean.
        :param max_length: The maximum amount of characters the box can hold before it no longer accepts any more
        characters from the user.
        :type max_length: Integer.
        """

        # Essential
        self.win_scale = win_scale

        self.interactive = interactive
        self.active = False
        self.tab_active = False
        self.private = private
        self.text_entered = False
        self.max_length = max_length +1

        self.text_surface_width_og = w

        if centre:
            self.text_box_rect = pg.Rect((x - 1/2*w) * win_scale, (y - 1/2*h) * win_scale, w * win_scale, h * win_scale)
        else:
            self.text_box_rect = pg.Rect(x * win_scale, y * win_scale, w * win_scale, h * win_scale)

        self.text_box_colour = (161, 161, 161)
        self.text_box_highlighted_colour = (240, 240, 240)
        self.text_color = (255, 255, 30)
        self.name = name
        self.display_text = name
        self.user_input = ''

        font_path = os.path.join('resources', 'fonts', 'ARCADECLASSIC.TTF')
        self.__font = pg.font.Font(font_path, font_size * win_scale)
        self.text_surface = self.__font.render(self.display_text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.text_box_rect.center)

    def update(self, events):
        """
        Updates the textbox. This includes changing the size of the box if it gets too small for the text and handling
        events.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None.
        """

        # Updates the textbox
        # Resize the box if the text is too long.
        text_width = self.text_surface.get_width()
        if text_width > self.text_box_rect.w - 10 * self.win_scale:
            self.text_box_rect.w += 10 * self.win_scale
            self.text_box_rect.x -= 5 * self.win_scale

        elif self.text_surface_width_og < text_width < self.text_box_rect.w - 20 * self.win_scale:
            self.text_box_rect.w -= 10 * self.win_scale
            self.text_box_rect.x += 5 * self.win_scale
        if self.interactive:
            for event in events:
                if event.type == pg.MOUSEBUTTONUP:
                    # If the user clicked on the input_box rect.
                    if self.text_box_rect.collidepoint(*event.pos):
                        # Toggle the active variable.
                        self.active = True
                        self.user_input = ''
                    else:
                        self.active = False
                        self.tab_active = False
                        self.text_entered = False

                if event.type == pg.KEYDOWN:
                    if self.active or self.tab_active:
                        if event.key == pg.K_BACKSPACE:
                            self.user_input = self.user_input[:-1]
                        elif event.key == pg.K_RETURN:
                            return self.user_input  # think about this yea
                        else:
                            # Only accepts characters between 46-123
                            if event.unicode.lower() in [chr(x) for x in range(46, 123)]:
                                if len(self.user_input) < self.max_length:
                                    self.user_input += event.unicode

        # Re-render the text.
        if len(self.user_input) == 0:
            self.display_text = self.name

        if len(self.user_input) > 0:
            self.text_entered = True
            if self.private:
                self.display_text = '*' * len(self.user_input)
            else:
                self.display_text = self.user_input
        else:
            self.text_entered = False

        self.text_surface = self.__font.render(self.display_text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.text_box_rect.center)

    def display(self, win):
        """
        Blits text and box to the screen.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :return: None.
        """

        # Blit the text.
        win.blit(self.text_surface, self.text_rect)
        # Blit the rect.
        pg.draw.rect(win, self.text_box_colour
                     if not (self.active or self.tab_active)
                     else self.text_box_highlighted_colour, self.text_box_rect, 2 * self.win_scale)

    def get_input(self):
        return self.user_input


class ErrorBox:
    def __init__(self, content, win_scale):
        """
        Error box are used for when there is an error that effects the game in a way the user would not expect.
        :param content: The text that will be outputted in the box.
        :type content: String.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        """

        # Essential
        self.win_scale = win_scale

        self.content = content

        self.box = Box((20, 196), (296, 40), (255, 255, 255), 2, win_scale)
        self.transparent_win = pg.Surface((296 * win_scale, 40 * win_scale))
        self.transparent_win.set_alpha(225)
        self.transparent_win.fill((161, 161, 161))
        self.text_surface = Word(content,
                                 [coord/win_scale for coord in self.box.rect.center],
                                 (255, 255, 130, 100),
                                 20,
                                 win_scale,
                                 centre=True
                                 )

    # try get rid of this stupid true false thing
    def update(self, events):
        """
        The only check that the error box performs is to see if a mouse button has been lifted up or a key has been
        pressed down. This is because when the user presses something it will disappear.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: List.
        :return: Boolean: True if the user has pressed any key or mouse button else False.
        """

        for event in events:
            if event.type in [pg.MOUSEBUTTONUP, pg.KEYDOWN]:
                return False
        return True

    def display(self, win):
        """
        Blits the box and text to the surface.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :return: None.
        """

        win.blit(self.transparent_win, (20 * self.win_scale, 196 * self.win_scale))
        self.box.display(win)
        self.text_surface.display(win)


class Button:
    def __init__(self, content, pos, dimensions, font_size, text_colour, width, win_scale, centre=False):
        """
        Buttons are used to allow the user to select certain outcomes or events. Buttons use the word class and the
        box class.
        :param content: The text that will be blitted inside the button's box.
        :param pos: (x, y) Contains the x and y coordinates of the box.
        :type pos: Tuple.
        :param dimensions: (w, h) Contains width and height of the box.
        :type dimensions: Tuple.
        :param font_size: Font Size.
        :type font_size: Integer.
        :param text_colour: (r, g, b) colour of text.
        :type text_colour: Tuple.
        :param width: Width of box. (thickness or line)
        :type width: Integer.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param centre: If True the button will be centred at x, y. Otherwise x, y will become the top left point of the
        button.
        :type centre: Boolean.
        """

        x, y = pos
        w, h = dimensions

        self.active = False
        self.click = False

        self.tab_active = False

        self.react_boxes = []

        self.box = Box((x, y), (w, h), (161, 161, 161), width, win_scale, centre=centre)
        self.highlight_box = Box((x, y), (w, h), (255, 255, 255), width, win_scale, centre=centre)

        if centre:
            pos = [coord/win_scale for coord in self.box.rect.center]
            self.text_surface = Word(content, pos, text_colour, font_size, win_scale, centre=centre)
        else:
            pos = [coord/win_scale for coord in self.box.rect.midright]
            self.text_surface = Word(content, pos, text_colour, font_size, win_scale, centre=centre)

    def update(self, events):
        """
        Checks whether the mouse is 'colliding' with the button's box and if the mouse has been clicked. It becomes
        active if it has been clicked (meaning the colour of the box will change). The program using the button must
        implement the button's function and can use the click attribute to decide when to execute the desired outcome.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: List.
        :return: None
        """

        pos = pg.mouse.get_pos()
        collision = self.check_mouse(*pos)
        click = False
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                click = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:
                    click = True

        self.click = collision and click

        if not self.tab_active:
            self.active = collision
        elif collision:
            self.tab_active = False

    def display(self, win):
        """
        Blits the box, and text to the win surface.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :return: None.
        """

        if self.active or self.tab_active:
            self.highlight_box.display(win)
        else:
            self.box.display(win)
        self.text_surface.display(win)

    def check_mouse(self, x, y):
        """
        Returns True if the (x, y) co-ord is within the box's rect.
        :param x: x coord of mouse.
        :param y: y coord of mouse.
        :return: True if (x, y) is colliding else False.
        """

        return self.box.check_mouse(x, y)

    def get_click(self):
        return self.click


class Slider:
    def __init__(self, content, x, y, w, h, font_size, text_colour, box_width, win_scale, centre=False, level=50,
                 levels=100):
        """
        Uses a box, a word and a transparent box to create a slider. It can be used by the user to select a level for
        something. The range is from 0 to the level's parameter. The default is 100 and this is mainly used for sound
        sliders, but the one for win scale, for example, only goes up to 5.
        :param content: The word that will be displayed in the slider (name of the slider).
        :param x: x coord of pos.
        :type x: Integer.
        :param y: y coord of pos.
        :type y: Integer.
        :param w: Width of box.
        :type w: Integer.
        :param h: Width of box.
        :type h: Integer.
        :param font_size: Font size.
        :type font_size: Integer.
        :param text_colour: (r, g, b) colour of the word / content.
        :type text_colour: Tuple.
        :param box_width: Width of box line.
        :type box_width: Integer.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param centre: If True the (x, y) coords will become the boxes centre else the (x, y) coords will be the boxes
        top left.
        :type centre: Boolean.
        :param level: The current level of the slider.
        :type level: Integer.
        :param levels: The maximum level of the slider.
        :type levels: Integer.
        """

        # Needed to move the slider
        self.x = x if not centre else x - 1/2 * w
        self.y = y if not centre else y - 1/2 * h
        self.w = w
        self.h = h

        self.win_scale = win_scale

        self.font_size = font_size
        self.text_colour = text_colour
        self.centre = centre

        self.react = False
        self.active = False
        self.click = False

        self.content = content

        self.levels = levels

        self.level = (level/levels) * w * win_scale

        self.level_string = level

        # Boxes (normal and highlighted)
        self.box = Box((x, y), (w, h), (161, 161, 161), box_width, win_scale, centre=centre)
        self.highlight_box = Box((x, y), (w, h), (255, 255, 255), box_width, win_scale, centre=centre)

        # Text
        self.text_surface = self.get_text()

        # Transparent slider
        self.slider = self.get_slider()

    def update(self, events):
        """
        Checks where on the slider the mouse has been clicked and adjusts the slider and word to match this value.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: Tuple.
        :return: None.
        """

        pos = pg.mouse.get_pos()
        collision = self.check_mouse(*pos)
        click = False
        if pg.mouse.get_pressed()[0]:
            click = True
        self.click = collision and click
        self.react = collision

        if self.click:
            x, y = pos
            self.level = x - self.x * self.win_scale
            self.level_string = round((self.level / (self.win_scale * self.w)) * self.levels)

        self.slider = self.get_slider()
        self.text_surface = self.get_text()

    def display(self, win):
        """
        Blits the transparent slider (PyGame surface object), the text, and the box to the screen. If react is True, then
        the highlighted (white) box will be blitted instead.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        win.blit(self.slider, (self.x * self.win_scale, self.y * self.win_scale))
        self.text_surface.display(win)

        if self.react:
            self.highlight_box.display(win)
        else:
            self.box.display(win)

    def get_text(self):
        """
        Instantiates a text object. This must be run every time the level is changed in order to update the number.
        :return: The word object.
        """

        text_surface = Word('{} {}'.format(self.content, self.level_string),
                            [coord / self.win_scale for coord in self.box.rect.center],
                            self.text_colour,
                            self.font_size,
                            self.win_scale,
                            centre=True
                            )
        return text_surface

    def get_slider(self):
        """
        Gets the transparent surface that will become the sliding element. This must be run every time the level changes
        in order display that change graphically as well.
        :return: Slider object.
        """

        slider = pg.Surface((self.level, self.h * self.win_scale))
        slider.set_alpha(225)
        slider.fill((130, 130, 130))
        return slider

    def check_mouse(self, x, y):
        return self.box.check_mouse(x, y)


class TransparentInputBox(InputBox):
    def __init__(self, w, h, font_size, win_scale, name=''):
        x = 168
        y = 226
        super().__init__(x, y, w, h, font_size, win_scale, name, True, True, False, 3)

        self.active = True

        self.transparent_win = pg.Surface((200 * win_scale, 100 * win_scale))
        self.transparent_win.set_alpha(225)
        self.transparent_win.fill((161, 161, 161))

        self.box = Box((168, 210), (200, 100), (230, 230, 230), 2, win_scale, centre=True)

    def display(self, win):
        win.blit(self.transparent_win, (68 * self.win_scale, 160 * self.win_scale))
        self.box.display(win)
        super().display(win)


class Icon:
    def __init__(self, pos, imgs, win_scale, sound=False, toggle=False, target_program=False):
        """
        Class for creating icons.
        :param pos: Position on the screen where the icon will be.
        :param imgs: Img(s). Either the icon image or if is is toggleable you will need more than one image.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param sound: If the icon controls sound then this is True.
        :param toggle: If this icon is a toggle (image changes after each press) this is True.
        :param target_program: If the icon should run a sub-program when clicked then the name should be passed here.
        """

        # Essential
        self.sound = sound
        self.toggle = toggle
        self.has_target = True if target_program is not False else False
        self.target_program = target_program
        self.sound_toggle = sound

        # Sound
        if self.sound:
            pg.mixer.music.play()

        x, y = pos
        self._imgs = [pg.transform.smoothscale(pg.image.load(img), (25 * win_scale, 25 * win_scale)) for img in imgs]
        self._rect = self._imgs[0].get_rect(bottomright=(x * win_scale, y * win_scale))
        self._image_num = 0

    def display(self, win):
        """
        Blits the icon to the screen using the position and imgs.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        win.blit(self._imgs[self._image_num], self._rect)

    def check_click(self, x, y):
        """
        Checks if the mouse coords are inside a rectangle.
        :param x: x-coord of mouse click
        :param y: y-coord of mouse click
        :return: True if mouse click is inside rect else False.
        """

        return self._rect.collidepoint(x, y)

    def action(self):
        """
        This usually runs when the check_click function returns True, and completes the icons desired action.
        :return: None
        """

        if self.toggle:
            self._image_num = abs(self._image_num - 1)

        if self.sound:
            if self.sound_toggle:
                pg.mixer.music.pause()
                self.sound_toggle = False
            else:
                pg.mixer.music.unpause()
                self.sound_toggle = True
