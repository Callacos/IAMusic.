from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

# Classe principale de l'application
class MonApplication(App):
    def build(self):
        # Création d'une mise en page
        layout = BoxLayout(orientation='vertical')

        # Création d'un label
        self.label = Label(text='Bienvenue dans mon application Kivy!', size_hint=(1, 0.2))

        # Création d'un bouton
        bouton = Button(text='Cliquez-moi!', size_hint=(1, 0.2))
        bouton.bind(on_press=self.changer_texte)

        # Ajout du label et du bouton à la mise en page
        layout.add_widget(self.label)
        layout.add_widget(bouton)

        return layout

    # Méthode pour changer le texte du label
    def changer_texte(self, instance):
        self.label.text = 'Vous avez cliqué sur le bouton!'

# Exécution de l'application
if __name__ == '__main__':
    MonApplication().run()
