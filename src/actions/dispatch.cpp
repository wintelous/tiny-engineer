#include "actions/dispatch.h"

#include <Arduino.h>

#include "actions/action_list.h"
#include "actions/pattern.h"
#include "api/commands.h"
#include "audio/audio.h"
#include "display/ip_overlay.h"
#include "settings/settings.h"

namespace {

void runEntry(const ActionEntry& entry) {
  switch (entry.doKind) {
    case ActionDo::Sound:
      (void)tryStartButtonEventSound(actionsSoundName(entry.sound));
      break;
    case ActionDo::Anim:
      (void)apiSetAnimation(entry.anim);
      break;
    case ActionDo::ShowIp:
      showIpOverlay(millis());
      break;
  }
}

}  // namespace

void actionsDispatch(const char* type) {
  if (type == nullptr || type[0] == '\0') {
    return;
  }

  const ActionList& actions = settingsActions();
  for (size_t i = 0; i < actions.count(); i++) {
    const ActionEntry& entry = actions.at(i);
    if (actionsPatternMatch(entry.on, type)) {
      runEntry(entry);
    }
  }
}
