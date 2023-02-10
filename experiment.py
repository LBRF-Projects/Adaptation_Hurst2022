# -*- coding: utf-8 -*-

__author__ = "Austin Hurst"

from math import sqrt
from random import randrange
from ctypes import c_int, byref

import sdl2
import klibs
from klibs import P
from klibs.KLExceptions import TrialException
from klibs.KLGraphics import fill, flip, blit
from klibs.KLGraphics import KLDraw as kld
from klibs.KLEventQueue import flush, pump
from klibs.KLUserInterface import any_key, mouse_pos, ui_request, hide_cursor
from klibs.KLUtilities import angle_between, point_pos, deg_to_px, px_to_deg
from klibs.KLUtilities import line_segment_len as linear_dist
from klibs.KLTime import CountDown, precise_time
from klibs.KLCommunication import message

from gamepad import gamepad_init,button_pressed
from gamepad_usb import get_all_controllers

# Define colours for use in the experiment
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MIDGREY = (128, 128, 128)
TRANSLUCENT_RED = (255, 0, 0, 96)

# Define constants for working with gamepad data
AXIS_MAX = 32768
TRIGGER_MAX = 32767


class MotorMapping(klibs.Experiment):

    def setup(self):

        # Initialize stimulus sizes and layout
        screen_h_deg = (P.screen_y / 2.0) / deg_to_px(1.0)
        fixation_size = deg_to_px(0.5)
        fixation_thickness = deg_to_px(0.06)
        self.cursor_size = deg_to_px(P.cursor_size)
        self.target_size = deg_to_px(0.3)
        self.target_dist_min = deg_to_px(3.0)
        self.target_dist_max = deg_to_px(screen_h_deg - 1.0)
        self.lower_middle = (P.screen_c[0], int(P.screen_y * 0.75))
        self.msg_loc = (P.screen_c[0], int(P.screen_y * 0.4))

        # Initialize task stimuli
        self.cursor = kld.Ellipse(self.cursor_size, fill=TRANSLUCENT_RED)
        self.target = kld.Ellipse(self.target_size, fill=WHITE)
        self.fixation = kld.FixationCross(
            fixation_size, fixation_thickness, rotation=45, fill=WHITE
        )

        # Initialize gamepad (if present)
        self.gamepad = None
        gamepad_init()
        controllers = get_all_controllers()
        if len(controllers):
            self.gamepad = controllers[0]
            self.gamepad.initialize()
            print(self.gamepad._info)
        self.txtm.add_style('debug', '0.3deg')

        # Define error messages for the task
        err_txt = {
            "too_soon": (
                "Too soon!\nPlease wait for the target to appear before responding."
            ),
            "too_slow": "Too slow!\nPlease try to respond faster.",
            "stick_mi": (
                "Joystick moved!\n"
                "Please try to only imagine moving the stick over the target\n"
                "without actually performing the movement."
            ),
            "stick_cc": (
                "Joystick moved!\n"
                "Please pull the trigger as soon as you see the target, without\n"
                "moving the cursor."
            ),
            "continue": "Press any button to continue.",
        }
        self.errs = {}
        for key, txt in err_txt.items():
            self.errs[key] = message(txt, blit_txt=False, align="center")

        # Insert practice block
        self.insert_practice_block(1, trial_counts=P.practice_trials)


    def block(self):
        # Hide mouse cursor if not already hidden
        hide_cursor()

        block_msgs = {
            "PP": (
                "For the next set of trials, please use the right stick to move the\n"
                "cursor over the target, then press one of the back triggers."
            ),
            "MI": (
                "For the next set of trials, please try to imagine what it would look\n"
                "and feel like to move the cursor over the target (without actually\n"
                "moving it), then press one of the back triggers when you have\n"
                "completed the imagined movement."
            ),
            "CC": (
                "For the next set of trials, please press one of the back triggers as\n"
                "soon as you see the target appear (without moving the joystick)."
            )
        }
        inverted_msg = (
            "Note that for this block, the joystick controls will be different:\n"
            "The left-right axis has been flipped, such that moving the stick left\n"
            "or right will have the opposite effect it used to."
        )
        direction_map = {
            'normal': ("up", "up", "right", "right"),
            'backwards': ("up", "down", "left", "right"),
            'inverted_x': ("up", "up", "left", "right"),
            'inverted_y': ("up", "down", "right", "right"),
        }

        # Handle different phases of the experiment
        block_sequence = ["practice", "training", "test"]
        self.phase = block_sequence[P.block_number - 1]
        if self.phase == "practice":
            self.joystick_map = P.training_mapping
            self.trial_type = "PP"
            block_msg = "This is a practice block.\n\n" + block_msgs["PP"]
        elif self.phase == "training":
            self.joystick_map = P.training_mapping
            self.trial_type = P.condition
            block_msg = block_msgs[self.trial_type]
        elif self.phase == "test":
            self.joystick_map = P.test_mapping
            self.trial_type = "PP"
            block_msg = block_msgs["PP"] + "\n\n" + inverted_msg

        # Show block start message
        msg = message(block_msg, blit_txt=False, align="center")
        msg2 = message("Press any button to start.", blit_txt=False)
        self.show_feedback(msg, duration=2.0, location=self.msg_loc)
        fill()
        blit(msg, 5, self.msg_loc)
        blit(msg2, 5, self.lower_middle)
        flip()
        wait_for_input(self.gamepad)
        

    def setup_response_collector(self):
        pass


    def trial_prep(self):

        # Generate trial factors
        self.target_dist = randrange(self.target_dist_min, self.target_dist_max)
        self.target_angle = randrange(0, 360, 1)
        self.target_loc = vector_to_pos(P.screen_c, self.target_dist, self.target_angle)
        self.target_onset = randrange(1000, 3000, 100)

        # Add timecourse of events to EventManager
        self.evm.register_ticket(['target_on', self.target_onset])
        self.evm.register_ticket(['timeout', self.target_onset + 15000])

        # Set mouse to screen centre, fill screen, wait for input
        mouse_pos(position=P.screen_c)
        #if P.trial_number > 1:
        #    msg = message("Press any button to continue.", blit_txt=False)
        #    fill(MIDGREY)
        #    blit(msg, 5, P.screen_c)
        #    flip()
        #    wait_for_input(self.gamepad)


    def trial(self):

        # Initialize trial response data
        movement_rt = None
        contact_rt = None
        response_rt = None
        initial_angle = None
        axis_data = []
        last_x, last_y = (-1, -1)

        # Get joystick mapping for the trial
        mod_x, mod_y = P.input_mappings[self.joystick_map]

        # Initialize trial stimuli
        fill(MIDGREY)
        blit(self.fixation, 5, P.screen_c)
        blit(self.cursor, 5, P.screen_c)
        flip()

        target_on = None
        over_target = False
        while self.evm.before('timeout'):
            q = pump(True)
            ui_request(queue=q)

            # Get latest joystick/trigger data from gamepad
            if self.gamepad:
                self.gamepad.update()

            # Filter, standardize, and possibly invert the axis & trigger data
            lt, rt = self.get_triggers()
            jx, jy = self.get_stick_position()
            input_time = precise_time()
            cursor_pos = (
                P.screen_c[0] + int(jx * self.target_dist_max * mod_x),
                P.screen_c[1] + int(jy * self.target_dist_max * mod_y)
            )

            # Handle input based on trial type and trial phase
            triggers_released = lt < 0.2 and rt < 0.2
            cursor_movement = linear_dist(cursor_pos, P.screen_c)
            if target_on and not movement_rt and cursor_movement > 0:
                movement_rt = input_time - target_on
                initial_angle = vector_angle(P.screen_c, cursor_pos)
            err = "NA"
            if cursor_movement > self.cursor_size:
                if self.trial_type == "MI":
                    err = "stick_mi"
                elif self.trial_type == "CC":
                    err = "stick_cc"
                elif self.trial_type == "PP" and not target_on:
                    err = "too_soon"
            if self.evm.before('target_on'):
                if not triggers_released:
                    err = "too_soon"

            # If the participant did something wrong, show them a feedback message
            if err != "NA":
                self.show_feedback(self.errs[err], duration=2.0)
                fill()
                blit(self.errs[err], 5, P.screen_c)
                blit(self.errs['continue'], 5, self.lower_middle)
                flip()
                wait_for_input(self.gamepad)
                if target_on:
                    # NOTE: Do we want to recycle stick MI/CC errors as well?
                    # If so, should we still record when people make these errors
                    # regardless?
                    break
                else:
                    # If target hasn't appeared yet, recycle the trial
                    raise TrialException("Recycling trial!")

            # Log continuous cursor x/y data for each frame
            if target_on and cursor_movement:
                # Only log samples where position actually changes (to save space)
                any_change = (cursor_pos[0] != last_x) or (cursor_pos[1] != last_y)
                if any_change:
                    axis_sample = (
                        int((input_time - target_on) * 1000), # timestamp
                        cursor_pos[0], # joystick x
                        cursor_pos[1], # joystick y
                    )
                    axis_data.append(axis_sample)
                last_x = cursor_pos[0]
                last_y = cursor_pos[1]
            
            # Actually draw stimuli to the screen
            fill()
            blit(self.fixation, 5, P.screen_c)
            if self.evm.after('target_on'):
                blit(self.target, 5, self.target_loc)
            blit(self.cursor, 5, cursor_pos)
            #if P.development_mode:
            #    self.show_gamepad_debug()
            flip()

            # Get timestamp for when target drawn to the screen
            if not target_on and self.evm.after('target_on'):
                target_on = precise_time()
                
            # Check if the cursor is currently over the target
            dist_to_target = linear_dist(cursor_pos, self.target_loc)
            if dist_to_target < (self.cursor_size / 2):
                # Get timestamp for when cursor first touches target
                if not contact_rt:
                    contact_rt = precise_time() - target_on
                # To prevent participants from holding triggers down while moving the
                # stick (making the task much easier), the experiment only counts the
                # cursor as being over the target if both triggers are released while
                # over it.
                triggers_released = lt < 0.2 and rt < 0.2
                if not over_target and triggers_released:
                    over_target = True
            else:
                over_target = False

            # If either trigger pressed when it is possible to respond, end the trial
            can_respond = over_target or self.trial_type != "PP"
            if can_respond and (lt > 0.5 or rt > 0.5):
                response_rt = precise_time() - target_on
                break

        # Show RT feedback for 1 second (may remove this)
        if response_rt:
            rt_sec = "{:.3f}".format(response_rt)
            feedback = message(rt_sec, blit_txt=False)
            self.show_feedback(feedback, duration=1.0)
        elif err == "NA":
            feedback = self.errs['too_slow']
            self.show_feedback(feedback, duration=2.0)

        # Write raw axis data to database
        if err == "NA":
            for timestamp, stick_x, stick_y in axis_data:
                dat = {
                    'participant_id': P.participant_id,
                    'block_num': P.block_number,
                    'trial_num': P.trial_number,
                    'time': timestamp,
                    'stick_x': stick_x,
                    'stick_y': stick_y,
                }
                self.db.insert(dat, table='gamepad')

        return {
            "block_num": P.block_number,
            "trial_num": P.trial_number,
            "trial_type": self.trial_type,
            "mapping": self.joystick_map,
            "target_onset": self.target_onset if target_on else "NA",
            "target_dist": px_to_deg(self.target_dist),
            "target_angle": self.target_angle,
            "movement_rt": "NA" if movement_rt is None else movement_rt * 1000,
            "contact_rt": "NA" if contact_rt is None else contact_rt * 1000,
            "response_rt": "NA" if response_rt is None else response_rt * 1000,
            "initial_angle": "NA" if initial_angle is None else initial_angle,
            "err": err,
            "target_x": self.target_loc[0],
            "target_y": self.target_loc[1],
        }


    def trial_clean_up(self):
        pass


    def clean_up(self):
        if self.gamepad:
            self.gamepad.close()


    def show_gamepad_debug(self):
        if not self.gamepad:
            return

        # Get latest axis info
        rs_x, rs_y = self.gamepad.right_stick()
        ls_x, ls_y = self.gamepad.left_stick()
        lt = self.gamepad.left_trigger()
        rt = self.gamepad.right_trigger()
        dpad_x, dpad_y = self.gamepad.dpad()

        # Blit axis state info to the bottom-right of the screen
        info_txt = "\n".join([
            "Left Stick: ({0}, {1})",
            "Right Stick: ({2}, {3})",
            "Left Trigger: {4}",
            "Right Trigger: {5}",
            "D-Pad: ({6}, {7})",
        ]).format(ls_x, ls_y, rs_x, rs_y, lt, rt, dpad_x, dpad_y)
        pad_info = message(info_txt, style='debug', blit_txt=False)
        blit(pad_info, 1, (0, P.screen_y))


    def show_feedback(self, msg, duration=1.0, location=None):
        feedback_time = CountDown(duration)
        if not location:
            location = P.screen_c
        while feedback_time.counting():
            ui_request()
            if self.gamepad:
                self.gamepad.update()
            fill()
            blit(msg, 5, location)
            flip()
        
    
    def get_stick_position(self):
        if self.gamepad:
            raw_x, raw_y = self.gamepad.right_stick()
        else:
            # If no gamepad, approximate joystick with mouse movement
            mouse_x, mouse_y = mouse_pos()
            scale_factor = AXIS_MAX / self.target_dist_max
            raw_x = int((mouse_x - P.screen_c[0]) * scale_factor)
            raw_y = int((mouse_y - P.screen_c[1]) * scale_factor)

        return joystick_scaled(raw_x, raw_y)

    
    def get_triggers(self):
        if self.gamepad:
            raw_lt = self.gamepad.left_trigger()
            raw_rt = self.gamepad.right_trigger()
        else:
            # If no gamepad, emulate trigger press with mouse click
            raw_lt, raw_rt = (0, 0)
            mouse_x, mouse_y = c_int(0), c_int(0)
            if sdl2.SDL_GetMouseState(byref(mouse_x), byref(mouse_y)) != 0:
                # Ignore mouse button down for first 100 ms to ignore start-trial click
                if self.evm.trial_time_ms > 100:
                    raw_lt, raw_rt = (32767, 32767)

        return (raw_lt / TRIGGER_MAX, raw_rt / TRIGGER_MAX)




def joystick_scaled(x, y, deadzone = 0.2):

    # Check whether the current stick x/y exceeds the specified deadzone
    amplitude = min(1.0, sqrt(x ** 2 + y ** 2) / AXIS_MAX)
    if amplitude < deadzone:
        return (0, 0)

    # Smooth/standardize output coordinates to be on a circle, by capping
    # maximum amplitude at AXIS_MAX and converting stick angle/amplitude
    # to coordinates.
    angle = angle_between((0, 0), (x, y))
    amp_new = (amplitude - deadzone) / (1.0 - deadzone)
    xs, ys = point_pos((0, 0), amp_new, angle, return_int=False)

    return (xs, ys)

    
def wait_for_input(gamepad=None):
    valid_input = [
        sdl2.SDL_KEYDOWN,
        sdl2.SDL_MOUSEBUTTONDOWN,
        sdl2.SDL_CONTROLLERBUTTONDOWN,
    ]
    flush()
    user_input = False
    while not user_input:
        if gamepad:
            gamepad.update()
        q = pump(True)
        ui_request(queue=q)
        for event in q:
            if event.type in valid_input:
                user_input = True
                break


def vector_angle(p1, p2):
    # Gets the angle of a vector relative to directly upwards
    return angle_between(p1, p2, rotation=-90, clockwise=True)


def vector_to_pos(origin, amplitude, angle, return_int=True):
    # Gets the (x,y) coords of a vector's endpoint given its origin/angle/length
    # (0 degrees is directly up, 90 deg. is directly right, etc.)
    return point_pos(origin, amplitude, angle, rotation=-90, clockwise=True)