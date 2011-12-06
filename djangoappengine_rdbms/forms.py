from django import forms

# Some options does not make sense, like pythonpath
EXCLUDED_OPTIONS = ["--pythonpath","--settings","--noinput"]

class CommandArgsForm(forms.Form):
    args = forms.CharField(required=False)

    
    @property
    def option_list(self):
        options = u""
        for option in self.command.option_list:
            #import debugger; debugger.pdb().set_trace()
            if unicode(option) not in EXCLUDED_OPTIONS:
                options += u" " + unicode(option)
            
        return options

    def __init__(self,*args,**kwargs):
        #import debugger; debugger.pdb().set_trace()
        if "command" in kwargs:
            self.command = kwargs["command"]
            del kwargs["command"]

        super(CommandArgsForm,self).__init__(*args,**kwargs)
    
        if self.command:
            self.fields['args'].help_text = self.option_list
