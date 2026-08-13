(() => {
    'use strict';

    const STORAGE_KEY = '3f-book.email-gate.v1';
    const API_SUBMISSION_ENABLED = false;
    const API_ENDPOINT = ''; // Set this when API_SUBMISSION_ENABLED is enabled.
    let inMemoryEmail = '';

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function readStoredEmail() {
        try {
            return window.localStorage.getItem(STORAGE_KEY) || inMemoryEmail;
        } catch (_) {
            return inMemoryEmail;
        }
    }

    function saveEmail(email) {
        inMemoryEmail = email;
        try {
            window.localStorage.setItem(STORAGE_KEY, email);
        } catch (_) {
            // Private browsing or storage restrictions still permit this page visit.
        }
    }

    async function submitEmailToApi(email) {
        if (!API_SUBMISSION_ENABLED || !API_ENDPOINT) {
            return;
        }

        const response = await window.fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });

        if (!response.ok) {
            throw new Error('Email submission failed.');
        }
    }

    function unlock() {
        document.documentElement.classList.add('email-gate-ready');
        document.querySelector('.email-gate')?.remove();
    }

    function showGate() {
        const gate = document.createElement('section');
        gate.className = 'email-gate';
        gate.setAttribute('aria-labelledby', 'email-gate-title');
        gate.innerHTML = `
            <div class="email-gate__card">
                <h1 id="email-gate-title">Read the book</h1>
                <p>Enter your email address to continue.</p>
                <form class="email-gate__form" novalidate>
                    <label class="visually-hidden" for="email-gate-input">Email address</label>
                    <input id="email-gate-input" name="email" type="email" autocomplete="email" required placeholder="you@example.com">
                    <button type="submit">Continue</button>
                </form>
                <span class="email-gate__error" aria-live="polite"></span>
            </div>`;

        const form = gate.querySelector('form');
        const input = gate.querySelector('input');
        const error = gate.querySelector('.email-gate__error');
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = input.value.trim();
            if (!isValidEmail(email)) {
                error.textContent = 'Please enter a valid email address.';
                input.focus();
                return;
            }

            try {
                await submitEmailToApi(email);
                saveEmail(email);
                unlock();
            } catch (_) {
                // Keep the visitor on the form if the future API rejects a submission.
                error.textContent = 'We could not save your email. Please try again.';
            }
        });

        document.body.append(gate);
        input.focus();
    }

    if (isValidEmail(readStoredEmail())) {
        unlock();
    } else {
        showGate();
    }
})();
