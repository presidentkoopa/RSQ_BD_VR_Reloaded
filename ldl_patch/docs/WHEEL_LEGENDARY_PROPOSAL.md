# RSQ Wheel: showing a LegenDoom legendary on a BD22 VR gun's card (proposal, no Wheel edits)

Status: proposal only. Nothing in `RSQ_UBQSeries/Wheel/` was changed. Rig findings below are "rig only, not
headset-confirmed".

## What the card shows today (with LegenDoom 3.0 + this patch)

Wheel already has a LegenDoom reader: `Wheel/zscript/wheel/wr_compat_legendoom.zs` (`wr_CompatLegenDoom.RarityOf`,
`EffectsOf`, `TierOf`), behind the options "LegenDoom Rarity" (`wr_ld_compat`) and "LegenDoom Effects Row"
(`wr_ld_effects`). It builds the token names from **the held weapon's own class name**:

    base = wr_Rig.familyRoot(w.GetClassName())        // "LDShotgun" for LegenDoom's gun
    rarity token = base .. "Legendary" .. Epic|Rare|Uncommon|Common
    effect token = base .. "Effect_" .. <Name>

That is right for LegenDoom's own guns (`LDShotgun` -> `LDShotgunLegendaryRare`, `LDShotgunEffect_Vampiric`). With
the patch, the gun in hand is BD22 VR's (`Shot_Gun`, `Rifle`, `BrutalPistol`, ...), so the reader looks for
`Shot_GunLegendaryRare` and `Shot_GunEffect_...`, which never exist. Result on the rig (probe `tools/probe_wheel`,
log `evidence/logs/pW.log`, lines `WCARD`): the card shows the BD22 gun's own name, icon and ammo exactly as without
LegenDoom, and **no rarity colour, no rarity word and no effects row**. The same read with the prefix taken from the
patch finds the rarity and the effect (line `WCARD with-service`).

## Where LegenDoom keeps rarity and effects (the fields Wheel reads)

All are inventory items on the **player** (not on the weapon), one set per LegenDoom weapon slot. `<P>` is the slot
prefix, one of `LDFists LDChainsaw LDPistol LDShotgun LDSuperShotgun LDChaingun LDRocketLauncher LDPlasmaRifle LDBFG9000`
(LegenDoom's ACS `weaponActors[]` / `effectCheckerPrefix[]` in `source/LEGENDINF.acs`).

| What | Token | Notes |
|---|---|---|
| has a legendary | `<P>EffectActive` | one legendary per slot; LegenDoom refuses a second |
| rarity | `<P>LegendaryCommon` / `Uncommon` / `Rare` / `Epic` | exactly one |
| effect | `<P>Effect_<Name>` | e.g. `LDShotgunEffect_Vampiric`; `<Name>` is LegenDoom's identifier |
| effect title | LANGUAGE `LD_FX_TITLE_<Name>` | e.g. "Vampiric", "Exorcist's" (LegenDoom's `LANGUAGE.effectname`) |
| effect text | LANGUAGE `LD_FX_DESCR_<Name>` | one or two lines (`LANGUAGE.effectdesc`), `\c` colour codes inside |
| rarity colour | Green / Blue / Purple / Orange | LegenDoom's `rarityColors[]` (CR_GREEN, CR_BLUE, CR_PURPLE, CR_ORANGE); Wheel's reader already uses the same four from the pickup glows |

## Proposal

1. **Find the prefix through the patch, softly.** The patch (this folder) registers `RSLDP_Service`:

        ServiceIterator.Find("RSLDP_Service") -> s.GetString / GetStringUI("ld_prefix", "<weapon class>")
        -> "LDShotgun" for Shot_Gun, PuristShot_Gun; "LDChaingun" for Rifle, DualRifles, MiniGun ...; "" otherwise

   In `wr_CompatLegenDoom`, where `base` is built: if the weapon's own `base .. "Legendary*"` / `"Effect_"` finds
   nothing, ask the service once and use its prefix. No LD or RSLDP class is named at compile time, so Wheel still
   compiles and runs alone, with LegenDoom alone (its own guns keep working through the class name) and with
   LegenDoom + this patch. A cached per-class answer keeps it to one lookup per gun.
2. **Card:** rarity colour as the card wash/halo (Wheel's existing `TierOf` path), the rarity word plus the
   legendary's title on the sheet's top row ("RARE  Vampiric"), from `LD_FX_TITLE_<Name>` via
   `StringTable.Localize`, falling back to the raw `<Name>` if the string is missing.
3. **Effect lines:** `LD_FX_DESCR_<Name>` on the data sheet under the title, wrapped to the sheet width, `\c`
   colour codes kept (they are LegenDoom's own highlighting). The existing "LegenDoom Effects Row" option keeps
   switching it off.
4. **Which effects actually work on BD22 VR guns:** the patch carries 56 of LegenDoom's effects (`tables.zs`
   `Implemented`); with the patch's default re-roll on, a BD22 VR gun only ever holds one of those. If Wheel wants to
   mark a carried effect, the patch can answer `GetString("ld_carried", "<Name>")` -> "1"/"" (not built; one line in
   `RSLDP_Service` if the owner wants it).

Nothing else in Wheel needs to change: name, icon and ammo already come from the BD22 VR gun itself.
