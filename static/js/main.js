let token;
let user;
let votes;  //처음에 가져오는 투표결과들
let uploadImageState = 'none' //아무것도 없을 때 이미지 상태
let voteState = 'none'
stateMsg = {
    'hot': '더워요',
    'good': '적당해요',
    'cold': '추워요',
    'none': '투표 해주세요'
}
stateCuteMsg = {
    'hot': '더웡',
    'good': '좋앙',
    'cold': '추웡'
}

$(document).ready(function () {
    token = $.cookie('token')
    user = JSON.parse($.cookie('user'))
    console.log(user)
    console.log(user['email'], user['nickname'])
    showState();
    getTemperature();

    $('#setForm').on('submit', function (e) {
        e.preventDefault();  // Prevents the form from submitting the traditional way
        let temperature = $('#temperature').val();
        changeTemperature(temperature);
    });

    $('#msgInputPop').on('submit', function (e) {
        e.preventDefault();  // Prevents the form from submitting the traditional way
        let message = $('#message').val();
        updateState(voteState, message)
    });

    $(document).on('mouseenter', '.profile-container', function () {
        $(this).find('.message').css('display', 'block')
    }).on('mouseleave', '.profile-container', function () {
        $(this).find('.message').css('display', 'none')
    });
});

document.addEventListener('DOMContentLoaded', () => {
    // Functions to open and close a modal
    function openModal($el) {
      $el.classList.add('is-active');
    }
  
    function closeModal($el) {
      $el.classList.remove('is-active');
    }
  
    function closeAllModals() {
      (document.querySelectorAll('.modal') || []).forEach(($modal) => {
        closeModal($modal);
      });
    }
  
    // Add a click event on buttons to open a specific modal
    (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
      const modal = $trigger.dataset.target;
      const $target = document.getElementById(modal);
  
      $trigger.addEventListener('click', () => {
        openModal($target);
      });
    });
  
    // Add a click event on various child elements to close the parent modal
    (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
      const $target = $close.closest('.modal');
  
      $close.addEventListener('click', () => {
        closeModal($target);
      });
    });
  
    // Add a keyboard event to close all modals
    document.addEventListener('keydown', (event) => {
      if (event.code === 'Escape') {
        closeAllModals();
      }
    });
  });

function logout() {
    $.removeCookie('user');
    $.removeCookie('token');
    window.location.href = "/login"
}

function showState() {
    $.ajax({
        type: "GET",
        url: "/api/votes",
        data: {},
        success: function (response) {
            votes = response
            show_profile('hot')
            show_profile('good')
            show_profile('cold')
            show_climate(votes['most'])
            showStateMessage()
        }
    })
}

function showStateMessage() {
    let most = votes['most']
    let messages = votes[most]
    let message = ''
    if (message.length > 0) {
        var randomIndex = Math.floor(Math.random() * messages.length);
        message = messages[randomIndex]['message']
    }
    message = message != '' ? message : stateMsg[most]
    $('#climateMessage').text(`[${message}]`)
}

function show_profile(state) {
    console.log(votes)
    for (let i = 0; i < votes[state].length; i++) {
        url = votes[state][i]['profile']
        voteMsg = votes[state][i]['message']
        message = voteMsg == "" ? stateCuteMsg[state] : voteMsg
        console.log(voteMsg, stateMsg[state])
        html_template = `
                    <div class="profile-container column is-half">
                        <figure class="image is-48x48">
                        <img class="profile is-rounded" src=${url}>
                        </figure>
                        <span class="message hide">${message}</span>
                    </div>
                `
        row = parseInt(i / 2)
        mod = i % 2
        console.log(row, mod)
        if (mod == 0) {
            $(`#${state} > .profiles`).append(`<div id=${state}${row} class="columns"></div>`)
        }
        $(`#${state}${row}`).append(html_template);
    }

}
function show_climate(state) {
    $.ajax({
        type: "GET",
        url: `/api/stateImages?state=${state}`,
        success: function (response) {
            console.log(response)
            let img_url = response['img_url']
            $('#climateImage').attr('src', img_url)
            let text = ""
            if (response['nickname'] != undefined) {
                text = response['nickname'] + ' 님 제공'
            }
            console.log(text)
            $('#climateImageUser').text(text)
        }
    })
}
// 상태 업데이트 함수
function updateState(newState, message) {
    $.ajax({
        type: 'POST',
        url: '/api/vote',
        data: JSON.stringify({ "state": newState, "email": user['email'], "message": message }),
        contentType: 'application/json',
        success: function (response) {
            if (response['result'] == 'success') {
                alert('투표 완료')
                window.location.reload()
            }
        }
    });
}

function uploadFile() {
    var formData = new FormData($('#uploadForm')[0]);
    formData.append('email', user['email'])
    formData.append('state', uploadImageState)
    console.log("전송", formData)
    $.ajax({
        url: '/api/uploadImage',
        type: 'POST',
        data: formData,
        processData: false, // 중요: 이 설정을 통해 jQuery가 데이터를 쿼리 문자열로 변환하는 것을 방지합니다.
        contentType: false, // 중요: FormData를 사용할 때는 'multipart/form-data'로 설정하되, 자동 생성되도록 둡니다.
        success: function (response) {
            console.log('File uploaded successfully:', response);
            alert("업로드 성공 !!")
        },
        error: function (jqXHR, textStatus, errorMessage) {
            console.log('Error uploading file:', errorMessage);
            alert("업로드 실패 !!")
        }
    });
    hidePop()
}

function changeTemperature(temperature) {
    data = {
        'email': user['email'],
        'temperature': temperature
    }
    console.log(user['email'])
    $.ajax({
        type: 'POST',
        url: '/api/set',
        data: JSON.stringify(data),
        contentType: 'application/json',
        success: function (response) {
            if (response['result'] == 'success') {
                alert('설정 완료')
                window.location.reload()
            }
        }
    });
}

function getTemperature(){
    $.ajax({
        type: 'GET',
        url: '/api/set',
        contentType: 'application/json',
        success: function (response) {
            let text = ""
            if (response['result'] == 'success') {
                text = `${response['lastTime']} 에 ${response['temperature']} 로 설정 `
            } else {
                text = "온도 설정을 안했어요."
            }
            $('#lastTemperature').text(text)
        }
    });
}

function handleFileSelect(state) {
    uploadImageState = state
    $('#uploadForm').css('display', 'block');
}

function showPop() {
    uploadImageState = 'none'
    $('#uploadForm').css('display', 'none');
}

function setVoteState(state) {
    voteState = state
}