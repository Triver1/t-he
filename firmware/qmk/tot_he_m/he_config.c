// Actuation settings: EEPROM storage, the VIA custom menu, and the split sync. See he_config.h.

#include "quantum.h"
#include "transactions.h"
#include "nvm_eeconfig.h"
#include "he_config.h"
#ifdef VIA_ENABLE
#    include "via.h"
#endif

he_config_t he_config = HE_CONFIG_DEFAULTS;

// keeps release shallower than actuation, so a key that fires can always let go again
static void he_config_clamp(he_config_t *c) {
    c->actuation_dmm  = MIN(MAX(c->actuation_dmm, HE_ACTUATION_DMM_MIN), HE_ACTUATION_DMM_MAX);
    c->release_dmm    = MIN(MAX(c->release_dmm, HE_RELEASE_DMM_MIN), c->actuation_dmm - HE_HYSTERESIS_DMM);
    c->rapid_trigger  = c->rapid_trigger != 0;
    c->rt_press_dmm   = MIN(MAX(c->rt_press_dmm, HE_RT_DMM_MIN), HE_RT_DMM_MAX);
    c->rt_release_dmm = MIN(MAX(c->rt_release_dmm, HE_RT_DMM_MIN), HE_RT_DMM_MAX);
    // the stick needs some room between its dead zone and full deflection
    c->stick_deadzone_dmm = MIN(MAX(c->stick_deadzone_dmm, HE_STICK_DEADZONE_DMM_MIN), HE_STICK_DEADZONE_DMM_MAX);
    c->stick_full_dmm     = MIN(MAX(c->stick_full_dmm, c->stick_deadzone_dmm + HE_STICK_RANGE_DMM_MIN), HE_TRAVEL_DMM);
}

// QMK calls this on a full EEPROM reset and whenever the block's version does not match (a first flash, or a
// change to the block's layout that bumped EECONFIG_KB_DATA_VERSION). It zeroes the block, which leaves learnt
// travel at 0 (none yet); the settings get their defaults.
void eeconfig_init_kb_datablock(void) {
    nvm_eeconfig_init_kb_datablock();
    he_config = HE_CONFIG_DEFAULTS;
    eeconfig_update_kb_datablock(&he_config, 0, sizeof(he_config));
}

// the USB half sends its settings to the other half; the receiving half keeps them in RAM only
static void he_config_receive(uint8_t in_len, const void *in, uint8_t out_len, void *out) {
    if (in_len == sizeof(he_config_t)) {
        memcpy(&he_config, in, sizeof(he_config_t));
        he_config_clamp(&he_config);
    }
}

void he_config_init(void) {
    eeconfig_read_kb_datablock(&he_config, 0, sizeof(he_config));
    he_config_clamp(&he_config);
    transaction_register_rpc(RPC_ID_HE_CONFIG, he_config_receive);
}

void keyboard_post_init_kb(void) {
    he_config_init();
    he_travel_load();
    keyboard_post_init_user();
}

// resent every HE_CONFIG_SYNC_MS rather than on change only, so a half plugged in later still gets the settings
void he_config_task(void) {
    static uint32_t last = 0;
    if (is_keyboard_master() && timer_elapsed32(last) >= HE_CONFIG_SYNC_MS) {
        last = timer_read32();
        transaction_rpc_send(RPC_ID_HE_CONFIG, sizeof(he_config), &he_config);
    }
}

#ifdef VIA_ENABLE
// VIA's id_bootloader_jump, which QMK leaves unhandled: lets the host restart a half into its UF2 bootloader, so
// new firmware can be flashed without reaching the BOOT button or a QK_BOOT key
bool via_command_kb(uint8_t *data, uint8_t length) {
    if (data[0] == id_bootloader_jump) {
        reset_keyboard();
        return true;
    }
    return false;
}

static uint8_t *he_config_field(uint8_t value_id) {
    switch (value_id) {
        case id_he_actuation:
            return &he_config.actuation_dmm;
        case id_he_release:
            return &he_config.release_dmm;
        case id_he_rapid_trigger:
            return &he_config.rapid_trigger;
        case id_he_rt_press:
            return &he_config.rt_press_dmm;
        case id_he_rt_release:
            return &he_config.rt_release_dmm;
        case id_he_stick_deadzone:
            return &he_config.stick_deadzone_dmm;
        case id_he_stick_full:
            return &he_config.stick_full_dmm;
        default:
            return NULL;
    }
}

// data = [ command_id, channel_id, value_id, value_data ]
void via_custom_value_command_kb(uint8_t *data, uint8_t length) {
    uint8_t *command_id = &data[0];
    uint8_t *value_id   = &data[2];
    uint8_t *value      = &data[3];
    if (data[1] != id_custom_channel) {
        *command_id = id_unhandled;
        return;
    }
    uint8_t *field = he_config_field(*value_id);
    switch (*command_id) {
        case id_custom_set_value:
            if (!field) {
                *command_id = id_unhandled;
                break;
            }
            *field = *value;
            he_config_clamp(&he_config);
            break;
        case id_custom_get_value:
            if (*value_id == id_he_side) {
                *value = is_keyboard_left();
                break;
            }
            if (!field) {
                *command_id = id_unhandled;
                break;
            }
            *value = *field;
            break;
        case id_custom_save:
            eeconfig_update_kb_datablock(&he_config, 0, sizeof(he_config));
            break;
        default:
            *command_id = id_unhandled;
            break;
    }
}
#endif
