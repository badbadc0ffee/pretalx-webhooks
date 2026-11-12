onReady(() => {
  document.querySelectorAll("[data-webhook-delete-button]").forEach((button) => {
    button.addEventListener("click", () => {
      const form = button.closest("[data-webhook-form]")
      const deleteField = form.querySelector(
        "[data-webhook-delete-field] input[type=checkbox]",
      )
      deleteField.checked = true
      form.querySelectorAll("[required]").forEach((field) => {
        field.required = false
      })
      form.hidden = true
    })
  })
})
