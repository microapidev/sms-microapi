var AlertBox = function (id, option) {
  this.show = function (msg) {
    if (msg === '' || typeof msg === 'undefined' || msg === null) {
      throw '"msg parameter is empty"';
    }
    else {
      var alertArea = document.querySelector(id);
      var alertBox = document.createElement('DIV');
      var alertContent = document.createElement('DIV');
      var alertClose = document.createElement('A');
      var alertClass = this;
      alertContent.classList.add('alert-content');
      alertContent.innerText = msg;
      alertClose.classList.add('alert-close');
      alertClose.setAttribute('href', '#');
      alertBox.classList.add('alert-box');
      alertBox.appendChild(alertContent);
      if (!option.hideCloseButton || typeof option.hideCloseButton === 'undefined') {
        alertBox.appendChild(alertClose);
      }
      alertArea.appendChild(alertBox);
      alertClose.addEventListener('click', function (event) {
        event.preventDefault();
        alertClass.hide(alertBox);
      });
      if (!option.persistent) {
        var alertTimeout = setTimeout(function () {
          alertClass.hide(alertBox);
          clearTimeout(alertTimeout);
        }, option.closeTime);
      }
    }
  };

  this.hide = function (alertBox) {
    alertBox.classList.add('hide');
    var disperseTimeout = setTimeout(function () {
      alertBox.parentNode.removeChild(alertBox);
      clearTimeout(disperseTimeout);
    }, 500);
  };
};

// Sample invoke
var alertShowMessage = document.querySelector('#alertShowMessage');
var alertMessageBox = document.querySelector('#alertMessageBox');
var alertbox = new AlertBox('#alert-area', {
  closeTime: 5000,
  persistent: false,
  hideCloseButton: false
});
var alertboxPersistent = new AlertBox('#alert-area', {
  closeTime: 5000,
  persistent: true,
  hideCloseButton: false
});
var alertNoClose = new AlertBox('#alert-area', {
  closeTime: 5000,
  persistent: false,
  hideCloseButton: true
});


$(".btnss").click(function () {
  event.preventDefault()
  let form_url = $("#form").attr("form-data-url")
  formdata = {}
  $(".modal").css("display", "block")
  $(".clear").css("display", "block")
  formdata["senderID"] = $('input[name=senderID]').val()
  formdata["receiver"] = $('input[name=receiver]').val()
  formdata["message"] = $('textarea[name=message]').val()
  formdata["provider"] = $('select[name=provider]').val()

  $.ajax({
    url: form_url,
    type: "POST",
    data: formdata,
    success: function (data) {
      if (data.details) {
        $(".clear").css("display", "none")
        $(".done").css("display", "block")
        alertbox.show(data.details);
        $("form")[0].reset()
      }
    },
  })

})


// BULK_SMS
$(".send").click(function () {
  event.preventDefault()
  let form_url = $("#form").attr("form-data-url")
  $(".modal").css("display", "block")
  $(".clear").css("display", "block")
  formdata = {}
  formdata["groupID"] = $('input[name=groupID]').val()
  formdata["message"] = $('textarea[name=message]').val()
  formdata["senderID"] = $('input[name=senderID]').val()
  formdata["provider"] = $('select[name=provider]').val()
  alert(formdata)

  $.ajax({
    url: form_url,
    type: "POST",
    data: formdata,
    success: function (data) {
      if (data.details) {
        $(".clear").css("display", "none")
        $(".done").css("display", "block")
        alertbox.show(data.details);
        $("form")[0].reset()
      }
    },
  })

})

$(".close").click(function () {
  $(".lds-dual-ring").css("display", "none")
  $(".modal").css("display", "none")
  $(".clear").css("display", "none")
  $(".done").css("display", "none")
})


$(".group").click(function() {
  event.preventDefault()
  let form_url = $("#form").attr("form-data-url")
  $(".modal").css("display", "block")
  $(".clear").css("display", "block")
  let formdata = {}
  formdata["senderID"] = $("input[name=senderID]").val()
  formdata["numbers"] = $("textarea[name=numbers]").val()
  formdata["groupname"] = $("input[name=groupname]").val()


  $.ajax({
    url: form_url,
    type: "POST",
    data: formdata,
    success: function(data) {
      if (data.details) {
        $(".clear").css("display", "none")
        $(".done").css("display", "block")
        alertbox.show(data.details);
        $("form")[0].reset()
      }
    }
  })

  
})