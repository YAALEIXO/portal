from django import forms


def radio_status_widget():
    """RadioSelect com o template Bootstrap (form-check-inline), pra campos
    de status tipo ativo/inativo."""
    widget = forms.RadioSelect()
    widget.template_name = "widgets/bootstrap_radio.html"
    return widget


def status_field(label="Status", ativado="Ativado", desativado="Desativado", initial=True):
    return forms.TypedChoiceField(
        label=label,
        choices=[(True, ativado), (False, desativado)],
        coerce=lambda valor: valor == "True",
        initial=initial,
        widget=radio_status_widget(),
    )


def checkbox_multiple_widget():
    """CheckboxSelectMultiple com template Bootstrap: sem isso, o Django aplica
    a classe do <input> (form-check-input) na <div> que envolve a lista toda,
    colapsando-a pra 1em de altura e fazendo o conteúdo sobrepor o que vem
    depois no layout (ex.: os botões de Salvar/Cancelar)."""
    widget = forms.CheckboxSelectMultiple()
    widget.template_name = "widgets/bootstrap_checkbox_multiple.html"
    return widget


def checklist_dropdown_widget():
    """CheckboxSelectMultiple recolhido num dropdown do Bootstrap: mostra um
    resumo do que está selecionado e só abre a lista de checkboxes ao
    clicar — pra listas longas que não devem ficar sempre expandidas."""
    widget = forms.CheckboxSelectMultiple()
    widget.template_name = "widgets/checklist_dropdown.html"
    return widget
