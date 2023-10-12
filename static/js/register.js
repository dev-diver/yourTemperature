// 간단한 회원가입 함수입니다.
// 아이디, 비밀번호, 닉네임을 받아 DB에 저장합니다.
function isValidEmail(email) {
    // 이메일 형식을 검증하는 정규 표현식
    var regex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return regex.test(email);
}
function register() {
    console.log($('#uploadForm'))
    var formData = new FormData()
    formData.append('file', $('#profile')[0].files[0])
    let email = $('#email').val()
    formData.append('email', email)
    if (!isValidEmail(email)) {
        alert("올바른 메일 형식을 입력해주세요.");
        return;
    }
    formData.append('password', $('#password').val())
    formData.append('nickname', $('#nickname').val())
    console.log(formData)
    $.ajax({
        type: "POST",
        url: "/api/register",
        data: formData,
        processData: false, // 중요: 이 설정을 통해 jQuery가 데이터를 쿼리 문자열로 변환하는 것을 방지합니다.
        contentType: false,
        success: function (response) {
            if (response['result'] == 'success') {
                alert('회원가입이 완료되었습니다.')
                window.location.href = '/login'
            } else {
                alert(response['msg'])
            }
        }
    })
}