(function () {
    "use strict";

    function persistColapso(colapsada) {
        try {
            localStorage.setItem("axion.portal.sidebar", colapsada ? "1" : "0");
        } catch (e) {
            /* localStorage indisponível (modo privado etc.) — só não persiste */
        }
    }

    document.querySelectorAll(".shell-collapse-toggle").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var colapsada = document.documentElement.classList.toggle("shell-collapsed");
            persistColapso(colapsada);
        });
    });

    function configurarDropdown(toggleId, panelId) {
        var toggle = document.getElementById(toggleId);
        var panel = document.getElementById(panelId);
        if (!toggle || !panel) return;

        toggle.addEventListener("click", function (e) {
            e.stopPropagation();
            var abrir = panel.hidden;
            document.querySelectorAll(".shell-empresa-menu, .shell-user-menu-panel").forEach(function (p) {
                p.hidden = true;
            });
            panel.hidden = !abrir;
            toggle.setAttribute("aria-expanded", abrir ? "true" : "false");
        });
    }

    configurarDropdown("shellEmpresaToggle", "shellEmpresaMenu");
    configurarDropdown("shellUserMenuToggle", "shellUserMenuPanel");

    document.addEventListener("click", function (e) {
        document.querySelectorAll(".shell-empresa-menu, .shell-user-menu-panel").forEach(function (panel) {
            if (panel.hidden || panel.contains(e.target)) return;
            panel.hidden = true;
        });
    });
})();
