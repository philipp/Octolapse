import time
import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.extruder import ExtruderTriggers
from octoprint_octolapse.extruder import ExtruderState
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import TimerTrigger


class Test_TimerTrigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.Settings.CurrentPrinter().auto_detect_position = False
        self.Settings.CurrentPrinter().origin_x = 0
        self.Settings.CurrentPrinter().origin_y = 0
        self.Settings.CurrentPrinter().origin_z = 0
        self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()

    def tearDown(self):
        del self.Settings
        del self.OctoprintPrinterProfile

    def CreateOctoprintPrinterProfile(self):
        return dict(
            volume=dict(
                width=250,
                depth=200,
                height=200,
                formFactor="Not A Circle",
                custom_box=False,
            )
        )

    def test_TimerTrigger(self):
        """Test the timer trigger"""
        # use a short trigger time so that the test doesn't take too long
        self.Settings.CurrentSnapshot().timer_trigger_seconds = 2
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = TimerTrigger(self.Settings)
        trigger.ExtruderTriggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None,
                                                    None)  # Ignore extruder
        trigger.RequireZHop = False  # no zhop required
        trigger.HeightIncrement = 0  # Trigger on any height change
        # test initial state
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # set interval time to 0, send another command and test again (should not trigger, no homed axis)
        trigger.IntervalSeconds = 0
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Home all axis and try again with interval seconds 1 - should not trigger since the timer will start after the home command
        trigger.IntervalSeconds = 2
        position.Update("g28")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # send another command and try again, should not trigger cause we haven't waited 2 seconds yet
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Set the last trigger time to 1 before the previous LastTrigger time(equal to interval seconds), should not trigger
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Set the last trigger time to 1 before the previous LastTrigger time(equal to interval seconds), should trigger
        trigger.TriggerStartTime = time.time() - 2.01
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

    def test_TimerTrigger_ExtruderTriggers(self):
        """Test All Extruder Triggers"""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # home the axis
        position.Update("G28")
        trigger = TimerTrigger(self.Settings)
        trigger.IntervalSeconds = 1
        trigger.RequireZHop = False  # no zhop required

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # Try on extruding start - previous position not homed, do not trigger
        trigger.ExtruderTriggers = ExtruderTriggers(
            True, None, None, None, None, None, None, None, None, None)
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # send another command, now the previous state has been homed, should trigger
        position.Update("AnotherCommandNowPreviousHomed")
        # set is extruding start, wont be set by the above command!
        position.Extruder.StateHistory[0].IsExtrudingStart = True
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on extruding
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, True, None, None, None, None, None, None, None, None)
        state.IsExtruding = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on primed
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, True, None, None, None, None, None, None, None)
        state.IsPrimed = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on retracting start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, True, None, None, None, None, None, None)
        state.IsRetractingStart = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on retracting
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, True, None, None, None, None, None)
        state.IsRetracting = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on partially retracted
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, True, None, None, None, None)
        state.IsPartiallyRetracted = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on retracted
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, True, None, None, None)
        state.IsRetracted = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on detracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, True, None, None)
        state.IsDetractingStart = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on detracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, None, True, None)
        state.IsDetracting = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

         # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on detracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, None, None, True)
        state.IsDetracted = True
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

    def test_TimerTrigger_ExtruderTriggerWait(self):
        """Test wait on extruder"""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # home the axis
        position.Update("G28")
        trigger = TimerTrigger(self.Settings)
        trigger.RequireZHop = False  # no zhop required
        trigger.IntervalSeconds = 1

        
        # Use on extruding start for this test.
        trigger.ExtruderTriggers = ExtruderTriggers(
            True, None, None, None, None, None, None, None, None, None)

        # set the extruder trigger
        position.Extruder.GetState(0).IsExtrudingStart = True
        # will not wait or trigger because not enough time has elapsed
        trigger.Update(position) 
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # add 1 second to the state and try again
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01

        # send another command and try again
        position.Update("PreviousPositionIsNowHomed")
        # set the extruder trigger
        position.Extruder.GetState(0).IsExtrudingStart = True
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))


    def test_TimerTrigger_LayerChange_ZHop(self):
        """Test the layer trigger for layer changes triggers"""
        self.Settings.CurrentSnapshot().timer_trigger_require_zhop = True
        self.Settings.CurrentPrinter().z_hop = .5
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = TimerTrigger(self.Settings)
        trigger.ExtruderTriggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None,
                                                    None)  # Ignore extruder
        trigger.IntervalSeconds = 1
        # test initial state
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # send commands that normally would trigger a layer change, but without all axis homed.
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # Home all axis and try again, wait on zhop
        position.Update("g28")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))
        position.Update("g0 x0 y0 z.2 e1")
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # try zhop
        position.Update("g0 x0 y0 z.7 ")

        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # extrude on current layer, no trigger (wait on zhop)
        position.Update("g0 x0 y0 z.7 e1")
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # do not extrude on current layer, still waiting
        position.Update("g0 x0 y0 z.7 ")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # partial hop, but close enough based on our printer measurement tolerance (0.005)
        position.Update("g0 x0 y0 z1.1999")
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))

        # creat wait state
        position.Update("g0 x0 y0 z1.3 e1")
        trigger.GetState(0).TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # move down (should never happen, should behave properly anyway)
        position.Update("g0 x0 y0 z.8")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # move back up to current layer (should NOT trigger zhop)
        position.Update("g0 x0 y0 z1.3")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # move up a bit, not enough to trigger zhop
        position.Update("g0 x0 y0 z1.795")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting(0))

        # move up a bit, just enough to trigger zhop
        position.Update("g0 x0 y0 z1.7951")
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting(0))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_TimerTrigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
