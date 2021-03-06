"""A simple GUI framework for Pygame.

This framework is not meant as a competitor to PyQt or other, perhaps more
formal, GUI frameworks. Instead, pygameui is but a simple framework for game
prototypes.

The app is comprised of a stack of scenes; the top-most or current scene is
what is displayed in the window. Scenes are comprised of Views which are
comprised of other Views. pygameui contains view classes for things like
labels, buttons, and scrollbars.

pygameui is a framework, not a library. While you write view controllers in the
form of scenes, pygameui will run the overall application by running a loop
that receives device events (mouse button clicks, keyboard presses, etc.) and
dispatches the events to the relevant view(s) in your scene(s).

Each view in pygameui is rectangular in shape and whose dimensions are
determined by the view's "frame". A view is backed by a Pygame surface.
Altering a view's frame requires that you call 'relayout' which will resize the
view's backing surface and give each child view a chance to reposition and/or
resize itself in response.

Events on views can trigger response code that you control. For instance, when
a button is clicked, your code can be called back. The click is a "signal" and
your code is a "slot". The view classes define various signals to which you
connect zero or more slots.

    a_button.on_clicked.connect(click_callback)

"""

AUTHOR = 'Brian Hammond <brian@fictorial.com>'
COPYRIGHT = 'Copyright (C) 2012 Fictorial LLC.'
LICENSE = 'MIT'

__version__ = '0.2.3'


import pygame

import pigame

from .alert import AlertView, show_alert, OK, CANCEL
from .button import Button
from .callback import Signal
from .checkbox import Checkbox
from .dialog import DialogView
from .flipbook import FlipbookView
from .grid import GridView
from .imagebutton import ImageButton
from .imageview import ImageView, SCALE_TO_FILL, view_for_image_named
from .label import Label, CENTER, LEFT, RIGHT, TOP, BOTTOM, WORD_WRAP, CLIP
from .listview import ListView
from .notification import NotificationView, UP, DOWN, IDLE
from .progress import ProgressView
from .render import fill_gradient, fillrect
from .resource import font_cache, image_cache, sound_cache, logger, get_font, get_image, scale_image, get_sound
from .scroll import HORIZONTAL, SCROLLBAR_SIZE, ScrollbarView, ScrollView, ScrollbarThumbView
from .select import SelectView
from .slider import HORIZONTAL, VERTICAL, SliderView
from .spinner import SpinnerView
from .textfield import TextField
from .view import View

from . import focus
from . import window
from . import scene
from . import theme

from .scene import Scene


import logging
logger = logging.getLogger(__name__)


Rect = pygame.Rect
window_surface = None
pitft = pigame.PiTft()


def init(name='', window_size=(320, 240)):
    logger.debug('init %s %s' % (__name__, __version__))
    pygame.init()
    logger.debug('pygame %s' % pygame.__version__)
    pygame.key.set_repeat(200, 50)
    global window_surface
    window_surface = pygame.display.set_mode(window_size)
    pygame.display.set_caption(name)
    window.rect = pygame.Rect((0, 0), window_size)
    theme.init()


def run():
    global pitft
    try:
        clock = pygame.time.Clock()
        elapsed = 0
        while True:
            dt = clock.tick(60)
            elapsed += dt
            if elapsed >500:
                if single_loop_run(dt):
                    import sys
                    sys.exit()
    except KeyboardInterrupt:
        del(pitft)
        pygame.quit()
        raise


def single_loop_run(dt):
    global pitft
    assert len(scene.stack) > 0
    down_in_view = None
    pitft.update()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            del(pitft)
            pygame.quit()
            return True

        mousepoint = pygame.mouse.get_pos()

        if e.type == pygame.MOUSEBUTTONDOWN:
            hit_view = scene.current.hit(mousepoint)
            logger.debug('hit %s' % hit_view)
            if (hit_view is not None and not isinstance(hit_view, scene.Scene)):
                focus.set(hit_view)
                down_in_view = hit_view
                pt = hit_view.from_window(mousepoint)
                hit_view.mouse_down(e.button, pt)
            else:
                focus.set(None)
        elif e.type == pygame.MOUSEBUTTONUP:
            hit_view = scene.current.hit(mousepoint)
            if hit_view is not None:
                if down_in_view and hit_view != down_in_view:
                    down_in_view.blurred()
                    focus.set(None)
                pt = hit_view.from_window(mousepoint)
                hit_view.mouse_up(e.button, pt)
            down_in_view = None
        elif e.type == pygame.MOUSEMOTION:
            if down_in_view and down_in_view.draggable:
                pt = down_in_view.from_window(mousepoint)
                down_in_view.mouse_drag(pt, e.rel)
            else:
                scene.current.mouse_motion(mousepoint)
        elif e.type == pygame.KEYDOWN:
            if focus.view:
                focus.view.key_down(e.key, e.unicode)
            else:
                scene.current.key_down(e.key, e.unicode)
        elif e.type == pygame.KEYUP:
            if focus.view:
                focus.view.key_up(e.key)
            else:
                scene.current.key_up(e.key)

    scene.current.update(dt/1000.0)
    scene.current.draw()
    window_surface.blit(scene.current.surface, (0, 0))
    pygame.display.flip()
