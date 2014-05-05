from . import appsettings as local_settings


def scatter_buttons(document_year):
    buttons = local_settings.SCATTER_BUTTONS[:]
    if document_year in buttons:
        pass
    else:
        for i, year in enumerate(buttons):
            if abs(year - document_year) < 10:
                buttons[i] = document_year
                break
        else:
            buttons.append(document_year)
        buttons.sort()
    return buttons
