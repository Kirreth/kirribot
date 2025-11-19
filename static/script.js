document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.config-section');
    const configContentArea = document.querySelector('.config-content-area');

    if (!navLinks.length || !sections.length) {
        // Abbruch, wenn Navigation oder Sektionen fehlen
        return;
    }

    // Funktion zum Anzeigen der Sektion und Aktualisieren des aktiven Links
    const showSection = (targetId) => {
        // 1. Alle Links auf inaktiv setzen
        navLinks.forEach(link => {
            link.classList.remove('nav-link-active');
        });

        // 2. Alle Sektionen ausblenden
        sections.forEach(section => {
            section.style.display = 'none';
        });

        // 3. Ziel-Sektion anzeigen
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            targetSection.style.display = 'flex'; // Oder 'block', je nach Layout-Stil
        }

        // 4. Aktuellen Link auf aktiv setzen
        const activeLink = document.querySelector(`.nav-link[href="#${targetId}"]`);
        if (activeLink) {
            activeLink.classList.add('nav-link-active');
        }
    };

    // Event Listener für die Navigation
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault(); // Standard-Sprung verhindern
            
            const targetId = link.getAttribute('href').substring(1); // #overview -> overview
            
            showSection(targetId);

            // URL-Hash aktualisieren, um Teilen zu ermöglichen
            history.pushState(null, '', `#${targetId}`);

            // Auf Mobilgeräten zur Sektion scrollen (optional)
            if (window.innerWidth < 1024 && configContentArea) {
                configContentArea.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Hash beim Laden der Seite oder bei Zurück/Weiter-Navigation überprüfen
    const checkHashAndShowSection = () => {
        const hash = window.location.hash.substring(1);
        if (hash) {
            showSection(hash);
        } else {
            // Standardmäßig die erste Sektion anzeigen (z.B. overview)
            showSection(sections[0].id);
        }
    };

    // Initialisierung beim Laden der Seite
    checkHashAndShowSection();
    window.addEventListener('hashchange', checkHashAndShowSection);
});

// Zusätzliche visuelle Funktion für den Speichern-Button (Feedback)
const saveButton = document.querySelector('.button-save');
if (saveButton) {
    saveButton.addEventListener('click', () => {
        // Simulation des Speichervorgangs
        saveButton.textContent = 'Wird gespeichert...';
        saveButton.classList.add('saving-state');
        saveButton.disabled = true;

        setTimeout(() => {
            saveButton.textContent = 'Erfolgreich gespeichert!';
            
            setTimeout(() => {
                saveButton.textContent = 'Einstellungen Speichern';
                saveButton.classList.remove('saving-state');
                saveButton.disabled = false;
            }, 1500); // Erfolgsmeldung 1,5s anzeigen
        }, 1000); // Speicherdauer 1s simulieren
    });
}