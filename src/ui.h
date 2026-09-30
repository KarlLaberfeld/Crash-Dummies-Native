#pragma once
#include "game.h"
namespace ticd {
struct UiAssets {
    std::array<uint8_t,256*64> tiles{};
    std::array<uint8_t,Width*Height> titleBackground{};
    std::array<std::array<uint8_t,1024>,6> titleMaps{};
    std::array<uint8_t,48> initialScores{};
    static UiAssets load(const std::wstring& path);
};
// Stationary title pages reconstructed from the original raster layout.
// Page animation, input and campaign presentation integration are pending.
std::array<uint8_t,Width*Height> renderTitle(const UiAssets& assets,int page,bool twoPlayers,int ticks);
}
