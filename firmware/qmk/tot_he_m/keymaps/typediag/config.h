#pragma once

// Wiring test that needs no tools: types a rest report into the focused text editor a few seconds after it is
// plugged in, then a press report HE_PRESS_WINDOW_MS later. The keys send nothing meanwhile.
#define HE_TYPE_REPORT
#define HE_PRESS_WINDOW_MS 45000
// slower typing: macOS drops characters when a keyboard types at full speed
#define TAP_CODE_DELAY 12
