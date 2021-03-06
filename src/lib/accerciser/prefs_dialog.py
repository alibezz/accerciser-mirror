'''
Defines the preferences dialog.

@author: Eitan Isaacson
@organization: Mozilla Foundation
@copyright: Copyright (c) 2006, 2007 Mozilla Foundation
@license: BSD

All rights reserved. This program and the accompanying materials are made 
available under the terms of the BSD which accompanies this distribution, and 
is available at U{http://www.opensource.org/licenses/bsd-license.php}
'''

import gtk
from i18n import _
import atk
import gconf
import node
from tools import parseColorString

class AccerciserPreferencesDialog(gtk.Dialog):
  '''
  Class that creates a preferences dialog.
  '''
  def __init__(self, plugins_view=None, hotkeys_view=None):
    '''
    Initialize a preferences dialog.
    
    @param plugins_view: Treeview of plugins.
    @type plugins_view: L{PluginManager._View}
    @param hotkeys_view: Treeview of global hotkeys.
    @type hotkeys_view: L{HotkeyTreeView}
    '''
    gtk.Dialog.__init__(self, _('accerciser Preferences'), 
                        buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
    self.connect('response', self._onResponse)
    self.set_default_size(500,250)
    notebook = gtk.Notebook()
    self.vbox.add(notebook)
    for view, section in [(plugins_view, _('Plugins')),
                          (hotkeys_view, _('Global Hotkeys'))]:
      if view is not None:
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(view)
        notebook.append_page(sw, gtk.Label(section))
    
    notebook.append_page(_HighlighterView(), gtk.Label(_('Highlighting')))
        
  def _onResponse(self, dialog, response_id):
    '''
    Callback for dialog responses, always destroy it.
    
    @param dialog: This dialog.
    @type dialog: L{AccerciserPreferencesDialog}
    @param response_id: Response ID recieved.
    @type response_id: integer
    '''
    dialog.destroy()

class _HighlighterView(gtk.Alignment):
  '''
  A container widget with the settings for the highlighter.
  '''
  def __init__(self):
    gtk.Alignment.__init__(self)
    self.set_padding(12, 12, 18, 12)
    self.gconf_cl = gconf.client_get_default()
    self._buildUI()

  def _buildUI(self):
    '''
    Programatically build the UI.
    '''
    table = gtk.Table(3, 2)
    table.set_col_spacings(6)
    self.add(table)
    labels = [None, None, None]
    controls = [None, None, None]
    labels[0] = gtk.Label(_('Highlight duration:'))
    controls[0] = gtk.SpinButton()
    controls[0].set_range(0.01, 5)
    controls[0].set_digits(2)
    controls[0].set_value(
      self.gconf_cl.get_float('/apps/accerciser/highlight_duration'))
    controls[0].set_increments(0.01, 0.1)
    controls[0].connect('value-changed', self._onDurationChanged)
    labels[1] = gtk.Label(_('Border color:'))
    controls[1] = self._ColorButton(node.BORDER_COLOR, node.BORDER_ALPHA)
    controls[1].connect('color-set', self._onColorSet, 'highlight_border')
    controls[1].set_tooltip_text(_('The border color of the highlight box'))
    labels[2] = gtk.Label(_('Fill color:'))
    controls[2] = self._ColorButton(node.FILL_COLOR, node.FILL_ALPHA)
    controls[2].connect('color-set', self._onColorSet, 'highlight_fill')
    controls[2].set_tooltip_text(_('The fill color of the highlight box'))

    for label, control, row in zip(labels, controls, range(3)):
      label.set_alignment(0, 0.5)
      table.attach(label, 0, 1, row, row + 1, gtk.FILL)
      table.attach(control, 1, 2, row, row + 1, gtk.FILL)

    for label, control in zip(map(lambda x: x.get_accessible(),labels),
                              map(lambda x: x.get_accessible(),controls)):
      label.add_relationship(atk.RELATION_LABEL_FOR, control)
      control.add_relationship(atk.RELATION_LABELLED_BY, label)

  def _onDurationChanged(self, spin_button):
    '''
    Callback for the duration spin button. Update gconf and the global variable
    in the L{node} module.

    @param spin_button: The spin button that emitted the value-changed signal.
    @type spin_button: gtk.SpinButton
    '''
    node.HL_DURATION = int(spin_button.get_value()*1000)
    self.gconf_cl.set_float('/apps/accerciser/highlight_duration',
                            spin_button.get_value())
                            

  def _onColorSet(self, color_button, gconf_key):
    '''
    Callback for a color button. Update gconf and the global variables
    in the L{node} module.

    @param color_button: The color button that emitted the color-set signal.
    @type color_button: l{_HighlighterView._ColorButton}
    @param gconf_key: the key name suffix for this color setting.
    @type gconf_key: string
    '''
    if 'fill' in gconf_key:
      node.FILL_COLOR = color_button.get_rgb_string()
      node.FILL_ALPHA = color_button.get_alpha_float()
    else:
      node.BORDER_COLOR = color_button.get_rgb_string()
      node.BORDER_ALPHA = color_button.get_alpha_float()
      
    self.gconf_cl.set_string('/apps/accerciser/' + gconf_key,
                             color_button.get_rgba_string())

  class _ColorButton(gtk.ColorButton):
    '''
    ColorButton derivative with useful methods for us.
    '''
    def __init__(self, color, alpha):
      gtk.ColorButton.__init__(self, gtk.gdk.color_parse(color))
      self.set_use_alpha(True)
      self.set_alpha(int(alpha*0xffff))
                               
    def get_rgba_string(self):
      '''
      Get the current color and alpha in string format.

      @return: String in the format of #rrggbbaa.
      @rtype: string.
      '''
      color = self.get_color()
      color_val = 0
      color_val |= color.red >> 8 << 24
      color_val |= color.green >> 8 << 16
      color_val |= color.blue >> 8 << 8
      color_val |= self.get_alpha() >> 8
      return \
          '#' + hex(color_val).replace('0x', '').replace('L', '').rjust(8, '0')

    def get_rgb_string(self):
      '''
      Get the current color in string format.

      @return: String in the format of #rrggbb.
      @rtype: string.
      '''
      color = self.get_color()
      color_val = 0
      color_val |= color.red >> 8 << 16
      color_val |= color.green >> 8 << 8
      color_val |= color.blue >> 8
      return \
          '#' + hex(color_val).replace('0x', '').replace('L', '').rjust(6, '0')
      
    def get_alpha_float(self):
      '''
      Get the current alpha as a value from 0.0 to 1.0.
      '''
      return self.get_alpha()/float(0xffff)
