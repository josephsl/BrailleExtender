# coding: utf-8
# configBE.py
# Part of BrailleExtender addon for NVDA
# Copyright 2016-2020 André-Abush CLAUSE, released under GPL.

from __future__ import unicode_literals
import os
import globalVars
from collections import OrderedDict

import addonHandler
addonHandler.initTranslation()
import braille
import config
import configobj
import inputCore
import languageHandler
from . import brailleTablesExt
from .common import *
from .oneHandMode import DOT_BY_DOT, ONE_SIDE, BOTH_SIDES
from .consts import CHOICE_none, CHOICE_dot7, CHOICE_dot8, CHOICE_dots78, CHOICE_tags, CHOICE_likeSpeech, CHOICE_enabled, CHOICE_disabled, CHOICE_liblouis, TAG_SEPARATOR, CHOICE_spacing

Validator = configobj.validate.Validator

CHANNEL_stable = "stable"
CHANNEL_testing = "testing"
CHANNEL_dev = "dev"

CHOICE_braille = "braille"
CHOICE_speech = "speech"
CHOICE_speechAndBraille = "speechAndBraille"
CHOICE_focus = "focus"
CHOICE_review = "review"
CHOICE_focusAndReview = "focusAndReview"
NOVIEWSAVED = chr(4)

outputMessage = dict([
	(CHOICE_none,             _("none")),
	(CHOICE_braille,          _("braille only")),
	(CHOICE_speech,           _("speech only")),
	(CHOICE_speechAndBraille, _("both"))
])

updateChannels = dict([
	(CHANNEL_stable,  _("stable")),
	(CHANNEL_dev,     _("development"))
])

focusOrReviewChoices = dict([
	(CHOICE_none,           _("none")),
	(CHOICE_focus,          _("focus mode")),
	(CHOICE_review,         _("review mode")),
	(CHOICE_focusAndReview, _("both"))
])

curBD = braille.handler.display.name
backupDisplaySize = braille.handler.displaySize
backupRoleLabels = {}
iniGestures = {}
iniProfile = {}
profileFileExists = gesturesFileExists = False

noMessageTimeout = True if 'noMessageTimeout' in config.conf["braille"] else False
outputTables = inputTables = None
preTables = []
postTables = []
if not os.path.exists(profilesDir): log.error('Profiles\' path not found')
else: log.debug('Profiles\' path (%s) found' % profilesDir)

def getValidBrailleDisplayPreferred():
	l = braille.getDisplayList()
	l.append(("last", _("last known")))
	return l

def getConfspec():
	global curBD
	curBD = braille.handler.display.name
	return {
		"autoCheckUpdate": "boolean(default=True)",
		"lastNVDAVersion": 'string(default="unknown")',
		"updateChannel": f"option({CHANNEL_dev}, {CHANNEL_stable}, {CHANNEL_testing}, default={addonUpdateChannel})",
		"lastCheckUpdate": "float(min=0, default=0)",
		"profile_%s" % curBD: 'string(default="default")',
		"keyboardLayout_%s" % curBD: "string(default=\"?\")",
		"modifierKeysFeedback": "option({CHOICE_none}, {CHOICE_braille}, {CHOICE_speech}, {CHOICE_speechAndBraille}, default={CHOICE_braille})".format(
			CHOICE_none=CHOICE_none,
			CHOICE_braille=CHOICE_braille,
			CHOICE_speech=CHOICE_speech,
			CHOICE_speechAndBraille=CHOICE_speechAndBraille
		),
		"beepsModifiers": "boolean(default=False)",
		"volumeChangeFeedback": "option({CHOICE_none}, {CHOICE_braille}, {CHOICE_speech}, {CHOICE_speechAndBraille}, default={CHOICE_braille})".format(
			CHOICE_none=CHOICE_none,
			CHOICE_braille=CHOICE_braille,
			CHOICE_speech=CHOICE_speech,
			CHOICE_speechAndBraille=CHOICE_speechAndBraille
		),
		"brailleDisplay1": 'string(default="last")',
		"brailleDisplay2": 'string(default="last")',
		"hourDynamic": "boolean(default=True)",
		"leftMarginCells_%s" % curBD: "integer(min=0, default=0, max=80)",
		"rightMarginCells_%s" % curBD: "integer(min=0, default=0, max=80)",
		"reverseScrollBtns": "boolean(default=False)",
		"autoScrollDelay_%s" % curBD: "integer(min=125, default=3000, max=42000)",
		"smartDelayScroll": "boolean(default=False)",
		"ignoreBlankLineScroll": "boolean(default=True)",
		"speakScroll": "option({CHOICE_none}, {CHOICE_focus}, {CHOICE_review}, {CHOICE_focusAndReview}, default={CHOICE_focusAndReview})".format(
			CHOICE_none=CHOICE_none,
			CHOICE_focus=CHOICE_focus,
			CHOICE_review=CHOICE_review,
			CHOICE_focusAndReview=CHOICE_focusAndReview
		),
		"stopSpeechScroll": "boolean(default=False)",
		"stopSpeechUnknown": "boolean(default=True)",
		"speakRoutingTo": "boolean(default=True)",
		"routingReviewModeWithCursorKeys": "boolean(default=False)",
		"tabSpace": "boolean(default=False)",
		f"tabSize_{curBD}": "integer(min=1, default=2, max=42)",
		"undefinedCharsRepr": {
			"method": f"integer(min=0, default=8)",
			"hardSignPatternValue": "string(default=??)",
			"hardDotPatternValue": "string(default=6-12345678)",
			"desc": "boolean(default=True)",
			"extendedDesc": "boolean(default=True)",
			"fullExtendedDesc": "boolean(default=False)",
			"showSize": "boolean(default=True)",
			"start": "string(default=[)",
			"end": "string(default=])",
			"lang": "string(default=Windows)",
			"table": "string(default=current)"
		},
		"viewSaved": "string(default=%s)" % NOVIEWSAVED,
		"reviewModeTerminal": "boolean(default=True)",
		"features": {
			"roleLabels": "boolean(default=True)"
		},
		"objectPresentation": {
			"propertiesOrder": 'string(default="states,value,name,roleText,description,keyboardShortcut,positionInfo,positionInfoLevel,row,columnHeaderText,column,current,placeholder,cellCoordsText")',
			"selectedElement": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_dots78})",
		},
		"documentFormatting": {
			"alignments": {
				"enabled": "boolean(default=True)",
				"left": f"option({CHOICE_none}, {CHOICE_spacing}, {CHOICE_tags}, default={CHOICE_tags})",
				"right": f"option({CHOICE_none}, {CHOICE_spacing}, {CHOICE_tags}, default={CHOICE_tags})",
				"center": f"option({CHOICE_none}, {CHOICE_spacing}, {CHOICE_tags}, default={CHOICE_tags})",
				"justified": f"option({CHOICE_none}, {CHOICE_spacing}, {CHOICE_tags}, default={CHOICE_tags})",
			},
			"attributes": {
				"enabled": "boolean(default=True)",
				"bold": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"italic": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"underline": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"strikethrough": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"text-position:sub": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"text-position:super": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"invalid-spelling": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
				"invalid-grammar": f"option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, {CHOICE_tags}, default={CHOICE_tags})",
			},
			"indentations": {
				"enabled": "boolean(default=True)",
			},
			"lists": {
				"showLevelItem": "boolean(default=True)",
			},
			"tags": {
				"invalid-spelling": "string(default=%s)" % TAG_SEPARATOR.join(["⣏⠑⣹", "⣏⡑⣹"]),
				"invalid-grammar": "string(default=%s)" % TAG_SEPARATOR.join(["⣏⠛⣹", "⣏⡛⣹"]),
				"bold": "string(default=%s)" % TAG_SEPARATOR.join(["⣏⠃⣹", "⣏⡃⣹"]),
				"italic": "string(default=%s)" % TAG_SEPARATOR.join(["⣏⠊⣹", "⣏⡊⣹"]),
				"underline": "string(default=%s)" % TAG_SEPARATOR.join(["⣏⠥⣹", "⣏⡥⣹"]),
				"strikethrough": "string(default=%s)" % TAG_SEPARATOR.join(["⣏⠅⣹", "⣏⡅⣹"]),
				"text-align:center": "string(default=%s)" % TAG_SEPARATOR.join(["⣏ac⣹", ""]),
				"text-align:justified": "string(default=%s)" % TAG_SEPARATOR.join(["⣏aj⣹", ""]),
				"text-align:left": "string(default=%s)" % TAG_SEPARATOR.join(["⣏al⣹", ""]),
				"text-align:right": "string(default=%s)" % TAG_SEPARATOR.join(["⣏ar⣹", ""]),
				"text-align:start": "string(default=%s)" % TAG_SEPARATOR.join(["⣏ad⣹", ""]),
				"text-position:sub": "string(default=%s)" % TAG_SEPARATOR.join(["_{", "}"]),
				"text-position:super": "string(default=%s)" % TAG_SEPARATOR.join(["^{", "}"]),
			},
			"lineNumber": f'option("{CHOICE_likeSpeech}", "{CHOICE_enabled}", "{CHOICE_disabled}", default="{CHOICE_likeSpeech}")',
		},
		"quickLaunches": {},
		"roleLabels": {},
		"advancedInputMode": {
			"stopAfterOneChar": "boolean(default=True)",
			"escapeSignUnicodeValue": "string(default=⠼)",
		},
		"oneHandedMode": {
			"enabled": "boolean(default=False)",
			"inputMethod": f"option({DOT_BY_DOT}, {BOTH_SIDES}, {ONE_SIDE}, default={ONE_SIDE})",
		},
		"tables": {
			"groups": {},
			"shortcuts": 'string(default="?")',
			"preferredInput": f'string(default="{config.conf["braille"]["inputTable"]}|unicode-braille.utb")',
			"preferredOutput": f'string(default="{config.conf["braille"]["translationTable"]}")',
		},
		"advanced": {
			"fixCursorPositions": "boolean(default=True)",
		},
	}

def getLabelFromID(idCategory, idLabel):
	if idCategory == 0: return braille.roleLabels[int(idLabel)]
	elif idCategory == 1: return braille.landmarkLabels[idLabel]
	elif idCategory == 2: return braille.positiveStateLabels[int(idLabel)]
	elif idCategory == 3: return braille.negativeStateLabels[int(idLabel)]

def setLabelFromID(idCategory, idLabel, newLabel):
	if idCategory == 0: braille.roleLabels[int(idLabel)] = newLabel
	elif idCategory == 1: braille.landmarkLabels[idLabel] = newLabel
	elif idCategory == 2: braille.positiveStateLabels[int(idLabel)] = newLabel
	elif idCategory == 3: braille.negativeStateLabels[int(idLabel)] = newLabel

def loadRoleLabels(roleLabels):
	global backupRoleLabels
	for k, v in roleLabels.items():
		try:
			arg1 = int(k.split(':')[0])
			arg2 = k.split(':')[1]
			backupRoleLabels[k] = (v, getLabelFromID(arg1, arg2))
			setLabelFromID(arg1, arg2, v)
		except BaseException as err:
			log.error("Error during loading role label `%s` (%s)" % (k, err))
			roleLabels.pop(k)
			config.conf["brailleExtender"]["roleLabels"] = roleLabels

def discardRoleLabels():
	global backupRoleLabels
	for k, v in backupRoleLabels.items():
		arg1 = int(k.split(':')[0])
		arg2 = k.split(':')[1]
		setLabelFromID(arg1, arg2, v[1])
	backupRoleLabels = {}

def loadConf():
	global curBD, gesturesFileExists, profileFileExists, iniProfile
	curBD = braille.handler.display.name
	try: brlextConf = config.conf["brailleExtender"].copy()
	except configobj.validate.VdtValueError:
		config.conf["brailleExtender"]["updateChannel"] = "dev"
		brlextConf = config.conf["brailleExtender"].copy()
	if "profile_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["profile_%s" % curBD] = "default"
	if "tabSize_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["tabSize_%s" % curBD] = 2
	if "leftMarginCells__%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["leftMarginCells_%s" % curBD] = 0
	if "rightMarginCells_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["rightMarginCells_%s" % curBD] = 0
	if "autoScrollDelay_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["autoScrollDelay_%s" % curBD] = 3000
	if "keyboardLayout_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["keyboardLayout_%s" % curBD] = "?"
	confGen = (r"%s\%s\%s\profile.ini" % (profilesDir, curBD, config.conf["brailleExtender"]["profile_%s" % curBD]))
	if (curBD != "noBraille" and os.path.exists(confGen)):
		profileFileExists = True
		confspec = config.ConfigObj("", encoding="UTF-8", list_values=False)
		iniProfile = config.ConfigObj(confGen, configspec=confspec, indent_type="\t", encoding="UTF-8")
		result = iniProfile.validate(Validator())
		if result is not True:
			log.exception("Malformed configuration file")
			return False
	else:
		if curBD != "noBraille": log.warn("%s inaccessible" % confGen)
		else: log.debug("No braille display present")

	limitCellsRight = int(config.conf["brailleExtender"]["rightMarginCells_%s" % curBD])
	if (backupDisplaySize-limitCellsRight <= backupDisplaySize and limitCellsRight > 0):
		braille.handler.displaySize = backupDisplaySize-limitCellsRight
	if config.conf["brailleExtender"]["tables"]["shortcuts"] not in brailleTablesExt.listTablesFileName(brailleTablesExt.listUncontractedTables()): config.conf["brailleExtender"]["tables"]["shortcuts"] = '?'
	if config.conf["brailleExtender"]["features"]["roleLabels"]:
		loadRoleLabels(config.conf["brailleExtender"]["roleLabels"].copy())
	initializePreferredTables()
	return True

def initializePreferredTables():
	global inputTables, outputTables
	inputTables, outputTables = brailleTablesExt.getPreferredTables()

def loadGestures():
	if gesturesFileExists:
		if os.path.exists(os.path.join(profilesDir, "_BrowseMode", config.conf["braille"]["inputTable"] + ".ini")): GLng = config.conf["braille"]["inputTable"]
		else: GLng = 'en-us-comp8.utb'
		gesturesBMPath = os.path.join(profilesDir, "_BrowseMode", "common.ini")
		gesturesLangBMPath = os.path.join(profilesDir, "_BrowseMode/", GLng + ".ini")
		inputCore.manager.localeGestureMap.load(gesturesBDPath())
		for fn in [gesturesBMPath, gesturesLangBMPath]:
			f = open(fn)
			tmp = [line.strip().replace(' ', '').replace('$', iniProfile["general"]["nameBK"]).replace('=', '=br(%s):' % curBD) for line in f if line.strip() and not line.strip().startswith('#') and line.count('=') == 1]
			tmp = {k.split('=')[0]: k.split('=')[1] for k in tmp}
		inputCore.manager.localeGestureMap.update({'browseMode.BrowseModeTreeInterceptor': tmp})

def gesturesBDPath(a = False):
	l = ['\\'.join([profilesDir, curBD, config.conf["brailleExtender"]["profile_%s" % curBD], "gestures.ini"]),
	'\\'.join([profilesDir, curBD, "default", "gestures.ini"])]
	if a: return "; ".join(l)
	for p in l:
		if os.path.exists(p): return p
	return '?'

def initGestures():
	global gesturesFileExists, iniGestures
	if profileFileExists and gesturesBDPath() != '?':
		log.debug('Main gestures map found')
		confGen = gesturesBDPath()
		confspec = config.ConfigObj("", encoding="UTF-8", list_values=False)
		iniGestures = config.ConfigObj(confGen, configspec=confspec, indent_type="\t", encoding="UTF-8")
		result = iniGestures.validate(Validator())
		if result is not True:
			log.exception("Malformed configuration file")
			gesturesFileExists = False
		else: gesturesFileExists = True
	else:
		if curBD != "noBraille": log.warn('No main gestures map (%s) found' % gesturesBDPath(1))
		gesturesFileExists = False
	if gesturesFileExists:
		for g in iniGestures["globalCommands.GlobalCommands"]:
			if isinstance(
					iniGestures["globalCommands.GlobalCommands"][g],
					list):
				for h in range(
						len(iniGestures["globalCommands.GlobalCommands"][g])):
					iniGestures[inputCore.normalizeGestureIdentifier(
						str(iniGestures["globalCommands.GlobalCommands"][g][h]))] = g
			elif ('kb:' in g and g not in ["kb:alt', 'kb:control', 'kb:windows', 'kb:control', 'kb:applications"] and 'br(' + curBD + '):' in str(iniGestures["globalCommands.GlobalCommands"][g])):
				iniGestures[inputCore.normalizeGestureIdentifier(str(
					iniGestures["globalCommands.GlobalCommands"][g])).replace('br(' + curBD + '):', '')] = g
	return gesturesFileExists, iniGestures


def getKeyboardLayout():
	if (config.conf["brailleExtender"]["keyboardLayout_%s" % curBD] is not None
	and config.conf["brailleExtender"]["keyboardLayout_%s" % curBD] in iniProfile['keyboardLayouts'].keys()):
		return iniProfile['keyboardLayouts'].keys().index(config.conf["brailleExtender"]["keyboardLayout_%s" % curBD])
	else: return 0


def getTabSize():
	size = config.conf["brailleExtender"]["tabSize_%s" % curBD]
	if size < 0: size = 2
	return size

# remove old config files
cfgFile = globalVars.appArgs.configPath + r"\BrailleExtender.conf"
cfgFileAttribra = globalVars.appArgs.configPath + r"\attribra-BE.ini"
if os.path.exists(cfgFile): os.remove(cfgFile)
if os.path.exists(cfgFileAttribra): os.remove(cfgFileAttribra)

if not os.path.exists(configDir): os.mkdir(configDir)
if not os.path.exists(os.path.join(configDir, "brailleDicts")): os.mkdir(os.path.join(configDir, "brailleDicts"))
