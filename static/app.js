$thumbsupBtn = $("#messages button")
$newMessageText = $("#newMessageText")
$newMessageSaveButton = $("#newMessageSaveButton")

$messages = $("#messages")


$thumbsupBtn.click(async function() {
    let $button = $(event.target)
    let msg_id = event.target.id
    msg_id = msg_id.slice(12)
    const response = await axios.post(`/users/add_like/${msg_id}`)


    $button.toggleClass('btn-primary')
    $button.toggleClass('btn-secondary')
})

$newMessageSaveButton.click(async function() {
    const response = await axios.post(`/messages/new`, {"text": $newMessageText.val()})
    message = response.data.message
    if (window.location.pathname === '/' | window.location.pathname.includes('/users')) {
        const newLi = `<li class="list-group-item">
        <a href="/messages/${message.id}" class="message-link"></a>
        <a href="/users/${message.user_id}">
          <img src="${message.image_url}" alt="" class="timeline-image">
        </a>
        <div class="message-area">
          <a href="/users/${message.user_id}">@${message.username}</a>
          <span class="text-muted">${message.timestamp}</span>
          <p>${message.text}</p>
        </div>
        </li>`
      $messages.prepend(newLi)
    }
    console.log(message.image_url)
})
