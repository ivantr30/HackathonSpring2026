function openModal(modalType, userId, username = null) {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });

    const modalId = `modal-${modalType}`;
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal ${modalId} not found`);
        return;
    }

    modal.innerHTML = '<div class="modal-content"><p>Загрузка...</p></div>';
    modal.style.display = 'block';

    let url = '';
    switch (modalType) {
        case 'edit-user':
            url = `/admin/users/${userId}/edit`;
            break;
        case 'change-password':
            url = `/admin/users/${userId}/change-password`;
            break;
        case 'assign-roles':
            url = `/admin/users/${userId}/assign-roles`;
            break;
        case 'delete-confirm':
            url = `/admin/users/${userId}/delete`;
            break;
        default:
            modal.innerHTML = '<div class="modal-content"><p>Неизвестный тип модального окна.</p></div>';
            return;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            modal.innerHTML = html;
            const form = modal.querySelector('form.ajax-form');
            if (form) {
                form.addEventListener('submit', handleFormSubmit);
            }
        })
        .catch(error => {
            console.error('Error loading modal:', error);
            modal.innerHTML = `<div class="modal-content"><p>Ошибка загрузки: ${error.message}</p></div>`;
        });
}

function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const url = form.action;
    const method = form.method;

    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            const modal = form.closest('.modal');
            if (modal) {
                modal.innerHTML = html;
                const newForm = modal.querySelector('form.ajax-form');
                if (newForm) {
                    newForm.addEventListener('submit', handleFormSubmit);
                }
            }
        })
        .catch(error => {
            console.error('Form submission error:', error);
            alert('Произошла ошибка при отправке формы.');
        });
}

function closeModal(modalType) {
    const modal = document.getElementById(`modal-${modalType}`);
    if (modal) {
        modal.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.modal-trigger').forEach(button => {
        button.addEventListener('click', function() {
            const modalType = this.dataset.modalType;
            const userId = this.dataset.userId;
            const username = this.dataset.username || null;
            openModal(modalType, userId, username);
        });
    });
});

window.addEventListener('click', function(event) {
    document.querySelectorAll('.modal').forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});