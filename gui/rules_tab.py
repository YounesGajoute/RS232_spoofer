"""
Spoofing Rules tab for RS232 Spoofer
Manages message modification rules
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import List, Dict, Any

class RulesTab:
    def __init__(self, parent_notebook, serial_manager):
        self.serial_manager = serial_manager
        
        # Create the tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Spoofing Rules")
        
        # Rules storage
        self.rules = []
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the rules management UI"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Rules list
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Rule editor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        self.setup_rules_list(left_frame)
        self.setup_rule_editor(right_frame)

    def setup_rules_list(self, parent):
        """Setup rules list section"""
        # Control frame
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Spoofing Rules", font=('TkDefaultFont', 12, 'bold')).pack(side=tk.LEFT)
        
        # Enable/disable spoofing
        self.spoofing_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Enable Spoofing", 
                       variable=self.spoofing_enabled,
                       command=self.on_spoofing_toggle).pack(side=tk.RIGHT)
        
        # Rules list
        list_frame = ttk.LabelFrame(parent, text="Active Rules")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for rules
        self.rules_tree = ttk.Treeview(list_frame, columns=('Type', 'Pattern', 'Enabled'), 
                                      show='tree headings', height=10)
        
        self.rules_tree.heading('#0', text='Description')
        self.rules_tree.heading('Type', text='Type')
        self.rules_tree.heading('Pattern', text='Pattern')
        self.rules_tree.heading('Enabled', text='Enabled')
        
        self.rules_tree.column('#0', width=150)
        self.rules_tree.column('Type', width=60)
        self.rules_tree.column('Pattern', width=100)
        self.rules_tree.column('Enabled', width=60)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.rules_tree.bind('<<TreeviewSelect>>', self.on_rule_selected)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="New Rule", command=self.new_rule).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Delete Rule", command=self.delete_rule).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Duplicate", command=self.duplicate_rule).pack(side=tk.LEFT, padx=2)
        
        # Import/Export buttons
        ttk.Separator(buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(buttons_frame, text="Import Rules", command=self.import_rules).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Export Rules", command=self.export_rules).pack(side=tk.LEFT, padx=2)

    def setup_rule_editor(self, parent):
        """Setup rule editor section"""
        editor_frame = ttk.LabelFrame(parent, text="Rule Editor")
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Rule properties
        props_frame = ttk.Frame(editor_frame)
        props_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Description
        ttk.Label(props_frame, text="Description:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.rule_description = ttk.Entry(props_frame, width=40)
        self.rule_description.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        
        # Type
        ttk.Label(props_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.rule_type = ttk.Combobox(props_frame, values=['ascii', 'hex'], state="readonly", width=10)
        self.rule_type.set('ascii')
        self.rule_type.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.rule_type.bind('<<ComboboxSelected>>', self.on_type_changed)
        
        # Enabled
        self.rule_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(props_frame, text="Enabled", variable=self.rule_enabled).grid(row=1, column=2, sticky=tk.W, padx=20, pady=2)
        
        props_frame.columnconfigure(1, weight=1)
        
        # Pattern section
        pattern_frame = ttk.LabelFrame(editor_frame, text="Pattern Matching")
        pattern_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Find Pattern:").pack(anchor=tk.W, padx=5, pady=2)
        self.rule_pattern = tk.Text(pattern_frame, height=3, wrap=tk.WORD)
        self.rule_pattern.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(pattern_frame, text="Replace With:").pack(anchor=tk.W, padx=5, pady=2)
        self.rule_replacement = tk.Text(pattern_frame, height=3, wrap=tk.WORD)
        self.rule_replacement.pack(fill=tk.X, padx=5, pady=2)
        
        # Help text
        self.help_text = ttk.Label(pattern_frame, text="ASCII mode: Enter text directly\nHEX mode: Enter hex bytes separated by spaces (e.g., 41 42 43)")
        self.help_text.pack(anchor=tk.W, padx=5, pady=5)
        
        # Test section
        test_frame = ttk.LabelFrame(editor_frame, text="Test Rule")
        test_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(test_frame, text="Test Data:").pack(anchor=tk.W, padx=5, pady=2)
        self.test_data = ttk.Entry(test_frame)
        self.test_data.pack(fill=tk.X, padx=5, pady=2)
        
        test_buttons = ttk.Frame(test_frame)
        test_buttons.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(test_buttons, text="Test Rule", command=self.test_rule).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_buttons, text="Clear", command=self.clear_test).pack(side=tk.LEFT, padx=2)
        
        self.test_result = ttk.Label(test_frame, text="", foreground="blue")
        self.test_result.pack(anchor=tk.W, padx=5, pady=2)
        
        # Save/Cancel buttons
        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save Rule", command=self.save_rule).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_edit).pack(side=tk.RIGHT, padx=2)
        
        # Current rule index
        self.current_rule_index = -1

    def on_spoofing_toggle(self):
        """Handle spoofing enable/disable"""
        enabled = self.spoofing_enabled.get()
        self.serial_manager.set_spoofing_enabled(enabled)

    def on_type_changed(self, event=None):
        """Handle rule type change"""
        rule_type = self.rule_type.get()
        if rule_type == 'ascii':
            help_text = "ASCII mode: Enter text directly"
        else:
            help_text = "HEX mode: Enter hex bytes separated by spaces (e.g., 41 42 43)"
        
        self.help_text.config(text=help_text)

    def on_rule_selected(self, event):
        """Handle rule selection"""
        selection = self.rules_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        rule_index = int(self.rules_tree.item(item_id)['values'][3])  # Hidden index
        
        if 0 <= rule_index < len(self.rules):
            self.load_rule_for_editing(rule_index)

    def new_rule(self):
        """Create a new rule"""
        self.clear_editor()
        self.current_rule_index = -1

    def delete_rule(self):
        """Delete selected rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this rule?"):
            item_id = selection[0]
            rule_index = int(self.rules_tree.item(item_id)['values'][3])  # Hidden index
            
            if 0 <= rule_index < len(self.rules):
                del self.rules[rule_index]
                self.update_rules_display()
                self.update_serial_manager_rules()
                self.clear_editor()

    def duplicate_rule(self):
        """Duplicate selected rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to duplicate.")
            return
        
        item_id = selection[0]
        rule_index = int(self.rules_tree.item(item_id)['values'][3])  # Hidden index
        
        if 0 <= rule_index < len(self.rules):
            rule_copy = self.rules[rule_index].copy()
            rule_copy['description'] = f"{rule_copy['description']} (Copy)"
            self.rules.append(rule_copy)
            self.update_rules_display()
            self.update_serial_manager_rules()

    def load_rule_for_editing(self, rule_index: int):
        """Load a rule into the editor"""
        if 0 <= rule_index < len(self.rules):
            rule = self.rules[rule_index]
            
            self.rule_description.delete(0, tk.END)
            self.rule_description.insert(0, rule.get('description', ''))
            
            self.rule_type.set(rule.get('type', 'ascii'))
            self.rule_enabled.set(rule.get('enabled', True))
            
            self.rule_pattern.delete(1.0, tk.END)
            self.rule_pattern.insert(1.0, rule.get('pattern', ''))
            
            self.rule_replacement.delete(1.0, tk.END)
            self.rule_replacement.insert(1.0, rule.get('replacement', ''))
            
            self.current_rule_index = rule_index
            self.on_type_changed()

    def clear_editor(self):
        """Clear the rule editor"""
        self.rule_description.delete(0, tk.END)
        self.rule_type.set('ascii')
        self.rule_enabled.set(True)
        self.rule_pattern.delete(1.0, tk.END)
        self.rule_replacement.delete(1.0, tk.END)
        self.test_data.delete(0, tk.END)
        self.test_result.config(text="")
        self.current_rule_index = -1

    def save_rule(self):
        """Save the current rule"""
        # Validate inputs
        description = self.rule_description.get().strip()
        if not description:
            messagebox.showerror("Validation Error", "Please enter a description.")
            return
        
        pattern = self.rule_pattern.get(1.0, tk.END).strip()
        if not pattern:
            messagebox.showerror("Validation Error", "Please enter a pattern.")
            return
        
        replacement = self.rule_replacement.get(1.0, tk.END).strip()
        
        rule_type = self.rule_type.get()
        
        # Validate hex format if needed
        if rule_type == 'hex':
            try:
                # Test pattern
                bytes.fromhex(pattern.replace(' ', ''))
                if replacement:
                    bytes.fromhex(replacement.replace(' ', ''))
            except ValueError:
                messagebox.showerror("Validation Error", "Invalid hex format. Use format like: 41 42 43")
                return
        
        # Create rule
        rule = {
            'description': description,
            'type': rule_type,
            'pattern': pattern,
            'replacement': replacement,
            'enabled': self.rule_enabled.get()
        }
        
        # Save rule
        if self.current_rule_index >= 0:
            # Update existing rule
            self.rules[self.current_rule_index] = rule
        else:
            # Add new rule
            self.rules.append(rule)
        
        self.update_rules_display()
        self.update_serial_manager_rules()
        self.clear_editor()
        
        messagebox.showinfo("Success", "Rule saved successfully.")

    def cancel_edit(self):
        """Cancel rule editing"""
        self.clear_editor()

    def test_rule(self):
        """Test the current rule"""
        pattern = self.rule_pattern.get(1.0, tk.END).strip()
        replacement = self.rule_replacement.get(1.0, tk.END).strip()
        test_data = self.test_data.get().strip()
        rule_type = self.rule_type.get()
        
        if not pattern or not test_data:
            self.test_result.config(text="Please enter pattern and test data.")
            return
        
        try:
            if rule_type == 'ascii':
                if pattern in test_data:
                    result = test_data.replace(pattern, replacement)
                    self.test_result.config(text=f"Match! Result: {result}", foreground="green")
                else:
                    self.test_result.config(text="No match found.", foreground="orange")
            else:  # hex
                # Convert test data to hex if it's ASCII
                if all(32 <= ord(c) <= 126 for c in test_data):
                    test_hex = ' '.join(f'{ord(c):02X}' for c in test_data)
                else:
                    test_hex = test_data
                
                pattern_bytes = bytes.fromhex(pattern.replace(' ', ''))
                replacement_bytes = bytes.fromhex(replacement.replace(' ', '')) if replacement else b''
                test_bytes = bytes.fromhex(test_hex.replace(' ', ''))
                
                if pattern_bytes in test_bytes:
                    result_bytes = test_bytes.replace(pattern_bytes, replacement_bytes)
                    result_hex = ' '.join(f'{b:02X}' for b in result_bytes)
                    self.test_result.config(text=f"Match! Result: {result_hex}", foreground="green")
                else:
                    self.test_result.config(text="No match found.", foreground="orange")
                    
        except Exception as e:
            self.test_result.config(text=f"Error: {str(e)}", foreground="red")

    def clear_test(self):
        """Clear test data and results"""
        self.test_data.delete(0, tk.END)
        self.test_result.config(text="")

    def update_rules_display(self):
        """Update the rules tree display"""
        # Clear existing items
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # Add rules
        for i, rule in enumerate(self.rules):
            enabled_text = "Yes" if rule.get('enabled', True) else "No"
            pattern_preview = rule.get('pattern', '')[:20]
            if len(rule.get('pattern', '')) > 20:
                pattern_preview += "..."
            
            self.rules_tree.insert('', tk.END, 
                                 text=rule.get('description', f'Rule {i+1}'),
                                 values=(rule.get('type', 'ascii'), 
                                        pattern_preview,
                                        enabled_text,
                                        i))  # Hidden index

    def update_serial_manager_rules(self):
        """Update rules in serial manager"""
        self.serial_manager.set_spoofing_rules(self.rules)

    def import_rules(self):
        """Import rules from JSON file"""
        filename = filedialog.askopenfilename(
            title="Import Rules",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    imported_rules = json.load(f)
                
                if isinstance(imported_rules, list):
                    self.rules.extend(imported_rules)
                    self.update_rules_display()
                    self.update_serial_manager_rules()
                    messagebox.showinfo("Success", f"Imported {len(imported_rules)} rules.")
                else:
                    messagebox.showerror("Error", "Invalid file format.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import rules: {str(e)}")

    def export_rules(self):
        """Export rules to JSON file"""
        if not self.rules:
            messagebox.showwarning("No Rules", "No rules to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Rules",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.rules, f, indent=2)
                
                messagebox.showinfo("Success", f"Exported {len(self.rules)} rules to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export rules: {str(e)}")
