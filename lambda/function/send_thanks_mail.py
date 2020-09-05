'''
# ************************************************* #
  Function : Sending thanks mails.
  Argument example :
{
  "recipient": "tomoki.m@world-avenue.com",
  "content": {
    "counselingForm": {
      "counselings": [
        "学校に通う期間",
        "滞在期間",
        "申込方法"
      ],
      "name": "世界 太郎",
      "nameFurigana": "セカイ タロウ",
      "way": "ZOOM",
      "age": 25,
      "prefecture": "北海道",
      "phone": "123-4567-8900",
      "others": "hogehogehogehogehoge"
    },
    "quotation": {
      "area": "シドニー",
      "courseId": "テストスクール1-テストキャンパス1_ワーキングホリデー_観光_シドニー_general-english_イブニング_パートタイム_20_10",
      "visa": "観光",
      "stay": 0,
      "pick": "False",
      "stayweeks": 4
    }
  }
}
  ※stay 0: 滞在手配希望する
        1: 滞在手配未定
        2: 滞在手配希望しない

  How to execute on local:
  1. Launch a mail server
    docker run --rm -it -e DEFAULT_REGION="ap-northeast-1" -e SERVICES="ses" -p 4567-4582:4567-4582 -p 8080:8080 localstack/localstack
  2. Execute this function
    docker run --rm -e DOCKER_LAMBDA_DEBUG=1 -p 9001:9001 -v "$PWD":/var/task lambci/lambda:python3.8 src.function.send_thanks_mail.lambda_handler '{"recipient": "koki.nakamura22@gmail.com", "content": {...}}'
# ************************************************* #
'''
import boto3
import os
from src.layer.common import myconst, lambda_to_lambda
from src.layer.common.environment import isDev, isSt
from src.layer.common.date import getTodayDateInJapan
from src.layer.mailer.mailer import sendHtmlMail, sendTextMail

nl = '\n'


def lambda_handler(event, context):
    # recipient
    recipient_user = event['recipient']
    recipient_staff = recipient_user if isDev() \
        else myconst.cst.FORM_MAIL_ADDRESS

    # subject
    username = event['content']['counselingForm']['name']
    subject_user = f"{username} 様 見積書の送付と留学カウンセリング仮予約完了のお知らせ【ワールドアベニュー】"
    subject_staff = f"【見積システム】{username}様よりカウンセリング予約"
    if isDev():
        subject_staff = f"【開発】{subject_staff}"
    elif isSt():
        subject_staff = f"【テスト】{subject_staff}"

    # body
    content = __getMailContents(event)
    text_body = __getTextBody(recipient_user, content)
    html_body = __getHtmlBody(recipient_user, content)

    # send a thanks email to Staff
    sendTextMail(recipient_staff, subject_staff, text_body)
    # send a thanks email to User
    sendHtmlMail(recipient_user, subject_user, html_body, None)


# get mail contents on the thanks mail
def __getMailContents(event):
    content = event['content']
    counselings = content['counselingForm']['counselings']
    counselingsStr = ''
    if not counselings == []:
        for c in counselings:
            counselingsStr += f"・{c}{nl}"
    content['counselingForm']['counselings'] = counselingsStr
    area = content["quotation"]["area"]
    arg = {
        "area": area,
        "courseId": content["quotation"]["courseId"]
    }
    response = lambda_to_lambda.executeLambdaSync('get_course', arg)
    course = response['body']
    arg = {
        "area": area,
        "school": course['school'],
        "pick": content["quotation"]["pick"],
        "weeks": content["quotation"]["stayweeks"]
    }
    response = lambda_to_lambda.executeLambdaSync('get_school_info', arg)
    school = response['body']
    arg = {
        "country": course['country'],
        "visa": content["quotation"]["visa"]
    }
    response = lambda_to_lambda.executeLambdaSync('get_country_info', arg)
    country = response['body']

    content['quotation'].update({'courseInfo': course})
    content['quotation'].update({'schoolInfo': school})
    content['quotation'].update({'countryInfo': country})
    return content


# get mail images from S3 bucket
def __getMailImages():
    images = {}
    s3 = boto3.client('s3')
    lambda_name = os.path.splitext(os.path.basename(__file__))[0]
    image_path = myconst.cst.S3_IMAGES_MAIL_PATH + lambda_name + '/'
    response = s3.list_objects_v2(
        Bucket=myconst.cst.S3BUCKET,
        Prefix=image_path
    )
    location = response['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']
    for fileobj in response['Contents']:
        if fileobj['Size'] > 0:
            url = "https://s3-%s.amazonaws.com/%s/%s" % (
                location, myconst.cst.S3BUCKET, fileobj['Key'])
            name = os.path.basename(fileobj['Key'])
            images[name] = url
    return images


def __formatMoney(money):
    return "{:,d}".format(money)


def __getToday():
    return getTodayDateInJapan().strftime("%Y年%m月%d日")


# get text body on the thanks mail
def __getTextBody(recipient,  content):
    username = content['counselingForm']['name']
    text_body = f"{username} 様より見積書送付依頼とカウンセリング予約がありました。{nl}{nl}"

    # カウンセリング予約内容
    text_body += f"◾️カウンセリング予約内容{nl}【相談内容】{nl}"
    text_body += f"{content['counselingForm']['counselings']}"
    text_body += f"【名前】{nl}"
    text_body += f"{username}（{content['counselingForm']['nameFurigana']}）{nl}"
    text_body += f"【カウンセリング方法】{nl}"
    text_body += f"{ content['counselingForm']['way']}{nl}"
    text_body += f"【年齢】{nl}"
    text_body += f"{ content['counselingForm']['age']}{nl}"
    text_body += f"【都道府県】{nl}"
    text_body += f"{ content['counselingForm']['prefecture']}{nl}"
    text_body += f"【Email】{nl}"
    text_body += f"{recipient}{nl}"
    text_body += f"【電話番号】{nl}"
    text_body += f"{ content['counselingForm']['phone']}{nl}"
    text_body += f"【その他相談事項】{nl}"
    text_body += f"{ content['counselingForm']['others']}{nl}{nl}"

    # 留学業務取扱料金合計
    applicationFee = content['quotation']['courseInfo']['applicationFee']
    # 学校コース料金 合計
    courseFee = content['quotation']['courseInfo']['totalCourseFeeJpy']
    # 滞在オプション合計
    accommodationFee = content['quotation']['schoolInfo']['accommodations'][0]['accommodationFeeJpy']
    # 留学代金合計
    studyAbroadFee = courseFee + accommodationFee
    # 全合計
    total = applicationFee + studyAbroadFee

    # 見積内容
    text_body += f"◾️見積内容{nl}"
    text_body += f"合計見積金額 {__formatMoney(total)}円（税込）{nl}"
    if 'promotion' in content['quotation']['courseInfo']['fees']:
        course = content['quotation']['courseInfo']['fees']['promotion']
        enrolment = course['pEnrolmentJpy']
        material = course['pMaterialJpy']
        tuition = course['pTuitionTotalJpy'] - course['pDiscountJpy']
        text_body += f"割引 {__formatMoney(content['quotation']['courseInfo']['totalDiscountJpy'])}円{nl}"
        text_body += f"{course['pValid']}までの申込限定{nl}{nl}"
    else:
        course = content['quotation']['courseInfo']['fees']['basic']
        enrolment = course['enrolmentJpy']
        material = course['materialJpy']
        tuition = course['tuitionTotalJpy']
        text_body += f"割引 なし{nl}{nl}"

    text_body += f"プログラム概要{nl}"
    if content['quotation']['visa'] == 'ワーキングホリデー':
        text_body += f"プログラム名：ワーキングホリデー{nl}"
    elif content['quotation']['visa'] == '観光' or '学生':
        text_body += f"プログラム名：語学留学{nl}"

    text_body += f"渡航国：{ content['quotation']['schoolInfo']['country']}{nl}"
    text_body += f"渡航都市：{ content['quotation']['schoolInfo']['area']}{nl}"
    text_body += f"ビザ：{content['quotation']['visa']}{nl}"
    text_body += f"就学期間：{content['quotation']['courseInfo']['weeks']}週間{nl}{nl}"

    text_body += f"留学業務取扱料金合計 ￥{__formatMoney(applicationFee)}{nl}{nl}"

    text_body += f"学校名：{content['quotation']['schoolInfo']['school']}{nl}"
    text_body += f"コース：{content['quotation']['courseInfo']['category']} {content['quotation']['courseInfo']['timetableType']} {content['quotation']['courseInfo']['timetable']}時間／週{nl}{nl}"

    text_body += f"学校コース料金内容{nl}"

    text_body += f"入学金 1回 ￥{__formatMoney(enrolment)}{nl}"
    text_body += f"教材費 ー ￥{__formatMoney(material)}{nl}"
    text_body += f"授業料 {content['quotation']['courseInfo']['weeks']}週間 ￥{__formatMoney(tuition)}{nl}{nl}"

    text_body += f"滞在オプション内容{nl}"
    if content['quotation']['stay'] == myconst.cst.STAY_OPTION_REQUEST:
        text_body += f"滞在手配 1回 ￥{__formatMoney(content['quotation']['schoolInfo']['accommodations'][0]['placementFeeJpy'])}{nl}"
        text_body += f"ホームステイ{content['quotation']['schoolInfo']['accommodations'][0]['roomType']} {content['quotation']['stayweeks']}週間 ￥{__formatMoney(content['quotation']['schoolInfo']['accommodations'][0]['stayFeeJpy'])}{nl}"
        if content['quotation']['pick'] == "True":
            text_body += f"空港送迎（片道）　1回　￥{__formatMoney(content['quotation']['schoolInfo']['accommodations'][0]['airportPickupFeeJpy'])}{nl}{nl}"
        else:
            text_body += f"空港送迎（片道）　0回　￥0{nl}{nl}"
    else:
        text_body += f"滞在手配　0回　￥0{nl}"
        text_body += f"ホームステイ{content['quotation']['schoolInfo']['accommodations'][0]['roomType']}　0週間　￥0{nl}"
        text_body += f"空港送迎（片道）　0回　￥0{nl}{nl}"

    text_body += f"留学代金合計　￥{__formatMoney(studyAbroadFee)}{nl}{nl}"

    text_body += f"見積に含まれていないもの{nl}"
    if 'materialNotice' in content['quotation']['schoolInfo']:
        text_body += f"{content['quotation']['schoolInfo']['school']}をお申込みの方へ{nl}"
        text_body += f"{content['quotation']['schoolInfo']['materialNotice']}{nl}"
    text_body += f"滞在費について{nl}"
    text_body += f"滞在オプションとしてご希望いただいたホームステイ期間以降の滞在費は含まれていません。また、ホームステイ開始は原則土日となり、平日開始はできません。平日到着に伴いホテルなどで宿泊される場合の滞在費はお客様のご負担となります。{nl}滞在方法や期間、また滞在に伴う費用は留学カウンセラーにご相談ください。{nl}{nl}"
    text_body += f"その他{nl}"
    text_body += f"{content['quotation']['countryInfo']['excludedInQuote']}{nl}{nl}"
    text_body += f"その他留意事項{nl}"
    if 'homestayNotice' or 'airportPickupNotice' in content['quotation']['schoolInfo']:
        text_body += f"{content['quotation']['schoolInfo']['school']}をお申込みの方へ{nl}"
        if 'homestayNotice' in content['quotation']['schoolInfo']:
            text_body += f"・ホームステイ ハイシーズン料金"
            text_body += f"{content['quotation']['schoolInfo']['homestayNotice']}{nl}"
        if 'airportPickupNotice' in content['quotation']['schoolInfo']:
            text_body += f"・空港送迎について"
            text_body += f"{content['quotation']['schoolInfo']['airportPickupNotice']}{nl}"
    text_body += f"{content['quotation']['countryInfo']['otherQuoteNotes']}{nl}{nl}"
    text_body += f"**{nl}"
    text_body += f"{__getToday()}時点での当社所定銀行 TTSレートに為替変動リスクヘッジを上乗せして計算いたしております。{nl}{nl}"
    text_body += f"当見積書は18歳以上を対象としています。"
    return text_body


# get html body on the thanks mail
def __getHtmlBody(recipient, content):
    images = __getMailImages()

    html_body = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style type="text/css">
        body {{
		font-family: 'Hiragino Kaku Gothic ProN','Meiryo',sans-serif;
		color:#222222;
		text-align: center;
		margin:0;
        padding:0;
        -ms-text-size-adjust: 100%;
        -webkit-text-size-adjust: 100%;
    	}}
        table {{
            border-spacing: 0;
        }}
    	table, td {{
    		border-collapse: collapse;
    		mso-table-lspace: 0;
    		mso-table-rspace: 0;
    	}}
    	img {{
    	  outline: none;
    	  border: none;
    	  text-decoration: none;
    	}}
    	a img {{
    	  border: none;
    	}}
    	.visible-xs-block{{
    				display: none !important;
    	}}
        .align-right{{
                    text-align: right;
        }}
        .w-th{{
            width: 200px;
        }}
        .w-space{{
            width: 200px;
        }}
        .w-price{{
            width: 200px;
        }}
        @media only screen and (max-width: 768px) {{
			.base {{
				width: 100% !important;
				min-width: 100% !important;
			}}
			td.responsive {{
				width: 100% !important;
				padding-left: 8px !important;
				padding-right: 8px !important;
				box-sizing: border-box !important;
				display: block !important;
			}}
			img {{
				/*width: 100% !important;*/
				max-width: 100% !important;
				height: auto !important;
			}}
			.visible-xs-block{{
				display: block !important;
			}}
			.hidden-xs{{
				display:none;
			}}
            .align-right{{
                text-align: left;
            }}
            .w-space{{
                width: 20%;
            }}
            .w-th{{
                width: 50%;
            }}
            .w-price{{
                width: 30%;
            }}
    	}}

        </style>
        </head>
        <body style='margin:0; padding:0;'>
         <table width='100%' border='0' align='center' cellpadding='0' cellspacing='0' bgcolor='#F8F9FA' class='base'>
            <tr>
             <td>
        
                <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#FEF6F2'>
                    <tr>
                        <td>
                            <table width='600' border='0' align='center' cellpadding='0' cellspacing='0' class='base'>
                                <tbody>
                                <tr>
                                    <td class='responsive' valign='top' align='left'><a href='https://www.world-avenue.co.jp/'><img src="{images['wa-logo.png']}" width='200' alt='ワールドアベニュー' /></a></td>
                                </tr>
                                </tbody>
                            </table> 
                        </td>
                    </tr>  
                </table>  
        <!-- wrap -->
        <table width='600' border='0' align='center' cellpadding='0' cellspacing='0' bgcolor='#fff' class='base'>
          <tr>
            <td>
    
            <table width='100%' border='0' cellpadding='0' cellspacing='0' bgcolor='#ffffff'>
                <tbody>
                    <tr>
                        <td valign='top' align='center'><img src='{images['kv.jpg']}' hspace='0' vspace='0' width='600' height='auto' style='width: 100%; max-width: 600px; height: auto;' alt='見積シミュレーションのご利用とカウンセリングの仮予約をいただきありがとうございました。' /></td>
                    </tr>
                </tbody>    
            </table>

      
              <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#ffffff'>
                  <tbody>
                      <tr>
                        <td class='responsive' valign='top' align='left'><font color='#222222' style='font-size: 15px; line-height:1.7; '>
                        { content['counselingForm']['name'] } 様<br /><br />海外留学サポートのワールドアベニューです。<br>
                        作成いただきました見積書の送付とカウンセリングの仮予約が完了したことをお知らせいたします。</font></td>
                      </tr>
                      <tr>
                        <td class='responsive' valign='top' align='left'><font color='#222222' style='font-size:15px; line-height:1.7; '>カウンセリング方法や日時のご案内に伴い担当カウンセラーよりあらためてご連絡をさせていただきます。今しばらくお待ちください。<br>
                        なお、48時間以内に担当者からお電話、またはメールでの連絡がない場合、ご入力いただいた内容に誤りがあるか、システムにエラーが発生している可能性がございます。下記のお問合せ先までご連絡いただきますようお願いいたします。</font></td>
                      </tr>
                      <tr>
                        <td class='responsive' valign='top' align='left'><font color='#222222' style='font-size: 15px; line-height:1.7; '><b>お問合せ</b><br>
                        フリーダイヤル：0120-623-385<br>
                        メールアドレス：japan@world-avenue.co.jp<br>
                        営業時間：11時〜21時｜定休日：毎週木曜</font></td>
                     </tr>
                  </tbody>
              </table>

              <table width='100%' border='0' cellpadding='0' cellspacing='0' bgcolor='#ffffff'>
                <tbody>
                    <tr><td height='20'></td></tr>
                    <tr>
                        <td width='5%'></td><td width='90%' class='responsive' valign='top' align='center' bgcolor='#FEF6F2' style='border-radius: 5px;padding:15px 5px;background-color: #FEF6F2;'><font color='#222222' style='font-size: 15px; line-height:1.7; '><b>送付内容</b><br> 1. カウンセリング仮予約内容 <br>2. 見積書（留学見積シミュレーション結果）</font></td><td width='5%'></td>
                    </tr>
                    <tr><td height='20'></td></tr>           
                </tbody>
              </table>
              

            <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#F8F9FA'>
                <tbody>
                    <tr><td height='10'></td></tr>
                    <tr>
                        <td class class='responsive' valign='top' align='center'><font color='#222222' style='font-size: 20px; font-weight:bold; line-height:1.5; '>1. 留学カウンセリング 仮予約内容</font></td>
                    </tr>
                    <tr><td height='10'></td></tr>
                </tbody>
            </table>   
        
            <table width='100%' border='0' align='center' cellpadding='10' cellspacing='0' bgcolor='#fff' class='base'>
                <tr>
                    <td>
                    <!-- table -->
                
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr>
                        <td nowrap class='responsive align-right' valign='top'><b>名前</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['name'] } 様</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>希望のカウンセリング方法</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['way'] }</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>年齢</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['age'] }歳</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>お住まいの都道府県</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['prefecture'] }</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>Email </b></td><td class='responsive' align='left' valign='top'>{recipient}</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>電話番号</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['phone'] }</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>相談したいこと</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['counselings'] }</td>
                        </tr>
                        <tr>
                            <td nowrap class='responsive align-right' valign='top'><b>その他相談事項</b></td><td class='responsive' align='left' valign='top'>{ content['counselingForm']['others'] }</td>
                        </tr>
                    </table>
                    
                    <!-- /table -->
                    </td>                        
                </tr>
            </table>

            <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#F8F9FA'>
                <tbody>
                    <tr><td height='10'></td></tr>
                    <tr>
                        <td class class='responsive' valign='top' align='center'><font color='#222222' style='font-size:20px; font-weight:bold; line-height:1.5; color: #222222;'>2. 見積書<br class='visible-xs-block'>（留学見積シミュレーション結果）</font></td>
                    </tr>
                    <tr><td height='10'></td></tr>
                </tbody>
            </table>   
        
       
            <table width='100%' border='0' cellpadding='20' cellspacing='0' bgcolor='#ffffff'>
                <tbody>
                <tr>"""
                    
    # 留学業務取扱料金合計
    applicationFee = content['quotation']['courseInfo']['applicationFee']
    # 学校コース料金 合計
    courseFee = content['quotation']['courseInfo']['totalCourseFeeJpy']
    # 滞在オプション合計
    accommodationFee = content['quotation']['schoolInfo']['accommodations'][0]['accommodationFeeJpy']
    # 留学代金合計
    studyAbroadFee = courseFee + accommodationFee
    # 全合計
    total = applicationFee + studyAbroadFee
    
    html_body += f"<td class='responsive' valign='top' align='center'><font color='#222222' style='font-size:20px; font-weight:bold; line-height:1.7; '>合計見積金額 {__formatMoney(total)}円</font><font color='#222222' style='font-size:14px;'>（税込）</font><br>"
        
    if 'promotion' in content['quotation']['courseInfo']['fees']:
        course = content['quotation']['courseInfo']['fees']['promotion']
        enrolment = course['pEnrolmentJpy']
        material = course['pMaterialJpy']
        tuition = course['pTuitionTotalJpy'] - course['pDiscountJpy']
        html_body += f"<font color='red' style='font-size:18px; font-weight:bold; line-height:1.7; color: red;'>割引 {__formatMoney(content['quotation']['courseInfo']['totalDiscountJpy'])}円</font><br>"
        html_body += f"<font color='red' style='color: red;'>{course['pValid']}までの申込限定</font></td></tr>"
    else:
        course = content['quotation']['courseInfo']['fees']['basic']
        enrolment = course['enrolmentJpy']
        material = course['materialJpy']
        tuition = course['tuitionTotalJpy']
        html_body += f"<font color='red' style='color: red;'>割引 なし</font></td></tr>"            
                    
    html_body += f"""</tbody>
            </table>
            
            <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#ffffff'>
                <tbody>
                    <tr>
                        <td class='responsive' valign='top' align='center'><font color='#222222' style='font-size:15px; line-height:1.7; '>注意事項<br>
                        お見積金額は為替の変動などに伴い随時変更となる可能性がございます。<br>
                        あくまで参考費用として留学のプランニングにお役立てください。<br>
                        留学プログラムをお申込みいただく際には担当カウンセラーより正式な見積書を別途発行いたします。</font></td>
                    </tr>
                </tbody>
            </table>
            <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#ffffff'>
                <tbody>
                    <tr>
                        <td class='responsive' valign='top' align='center'><font color='#222222' style='font-size:20px; border-bottom:1px solid #222; font-weight:bold; line-height:1.7; color: #222222;'>見積詳細</font></td>
                    </tr>
                </tbody>
            </table>

            <table width='100%' border='0' align='center' cellpadding='10' cellspacing='0' bgcolor='#fff' class='base'>
                <tr>
                    <td>
                    <!-- table -->
                    
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr style='border-bottom: 6px double #222222;'>
                            <td align='left' class='responsive' valign='top'><font color='#222222' style='font-size:16px; font-weight:bold; line-height:1.7; '>プログラム概要</font></td>
                        </tr>
                    </table>    
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>"""

    if content['quotation']['visa'] == 'ワーキングホリデー':
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap class='responsive' align='left' valign='top'><b>プログラム名</b></td><td class='responsive align-right' valign='top'>ワーキングホリデー</td></tr>"
    elif content['quotation']['visa'] == '観光' or '学生':
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap class='responsive' align='left' valign='top'><b>プログラム名</b></td><td class='responsive align-right' valign='top'>語学留学</td></tr>"

    html_body += f"""<tr style='border-bottom:1px solid #bdbdbd;'>
                        <td nowrap class='responsive' align='left' valign='top'><b>渡航国</b></td><td class='responsive align-right' valign='top'>{ content['quotation']['schoolInfo']['country'] }</td>
                        </tr>
                    <tr style='border-bottom:1px solid #bdbdbd;'>
                        <td nowrap class='responsive' align='left' valign='top'><b>渡航都市</b></td><td class='responsive align-right' valign='top'>{ content['quotation']['schoolInfo']['area'] }</td>
                    </tr>
                    <tr style='border-bottom:1px solid #bdbdbd;'>
                        <td nowrap class='responsive' align='left' valign='top'><b>ビザ（査証）</b></td><td class='responsive align-right'valign='top'>{ content['quotation']['visa'] }</td>
                    </tr>
                    <tr style='border-bottom:1px solid #bdbdbd;'>
                        <td nowrap class='responsive' align='left' valign='top'><b>就学期間</b></td><td class='responsive align-right' valign='top'>{content['quotation']['courseInfo']['weeks']}週</td>
                    </tr>
                    
                </table>
                
                <!-- /table -->
             </td>                        
           </tr>
        </table>

        <table width='100%' border='0' align='center' cellpadding='10' cellspacing='0' bgcolor='#fff' class='base'>
            <tr>
                <td>
                    <!-- table -->
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr style='border-bottom:6px double #222222;'>
                            <td align='left' class='responsive' valign='top'><font color='#222222' style='font-size:16px; font-weight:bold; line-height:1.7; '>留学業務取扱料金※</font></td>
                        </tr>
                    </table>
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr>
                            <td nowrap align='left' valign='top'><b>国内手続きサポート料金</b></td><td></td><td align='right' valign='top'>￥30,000</td>
                        </tr>
                    </table>   
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'> 
                        <tr>
                            <td class='w-space'></td><td class='w-th' align='right' bgcolor='#FEF6F2' valign='top'>小計</td><td class='w-price' bgcolor='#F8F9FA' align='right' valign='top'>￥30,00</td>
                        </tr>
                        <tr>
                            <td class='w-space'></td><td class='w-th' align='right' valign='top'>消費税及び地方消費税</td><td class='w-price' align='right' valign='top'>￥3,000</td>
                        </tr>
                        <tr>
                            <td class='w-space'></td><td class='w-th' align='right' align='left' bgcolor='#FEF6F2' valign='top'><b>留学業務取扱料金 合計</b></td><td class='w-price' bgcolor='#F8F9FA' align='right' valign='top'><b>￥{__formatMoney(content['quotation']['courseInfo']['applicationFee']) }</b></td>
                        </tr>
                    </table>  
                    <table border='0' width='100%' cellspacing='0' cellpadding='0' style='font-size:15px;line-height:1.7;'> 
                        <tr>
                            <td height='10'></td>
                        </tr>
                        <tr>
                            <td align='left' ><font color='#222222' style='font-size:15px; font-weight:bold; line-height:1.7;'>※留学業務取扱料金（国内手続きサポート料金）に含まれるサポート内容につい<a href='https://www.world-avenue.co.jp/service/support/kokunai-support' style='color:#0000FF;' target='_blank'>詳しくはこちら</a></font></td>
                        </tr>
                    </table>                       
                    <!-- /table -->
                </td>                        
            </tr>
        </table>

        <table width='100%' border='0' align='center' cellpadding='10' cellspacing='0' bgcolor='#fff' class='base'>
            <tr>
                <td>
                    <!-- table -->
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr style='border-bottom: 6px double #222222;'>
                            <td align='left' class='responsive' valign='top'><font color='#222222' style='font-size:16px; font-weight:bold; line-height:1.7; '>留学代金</font></td>
                        </tr>
                        <tr>
                            <td align='left'><font color='#222222' style='font-size:15px; font-weight:bold; line-height:1.7; '>{ content['quotation']['schoolInfo']['school'] }<br>
                                { content['quotation']['courseInfo']['category'] } { content['quotation']['courseInfo']['timetableType'] } { content['quotation']['courseInfo']['timetable'] }時間／週</font></td>
                        </tr>
                    </table>
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr style='background-color: #F8F9FA;'>
                            <td nowrap align='left' valign='top'><b>学校コース料金内容</b></td><td align='right' valign='top'><b>期間／回</b></td><td align='right' valign='top'><b>期間／回</b></td>
                        </tr>
                        <tr style='border-bottom:1px solid #bdbdbd;'>
                            <td nowrap align='left' valign='top'><b>入学金</b></td><td align='right' valign='top'>1回</td><td align='right' valign='top'>￥{__formatMoney( content['quotation']['courseInfo']['fees']['promotion']['pEnrolmentJpy'])}</td>
                        </tr>
                        <tr style='border-bottom:1px solid #bdbdbd;'>
                            <td nowrap align='left' valign='top'><b>教材費</b></td><td align='right' valign='top'>-</td><td align='right' valign='top'>￥{__formatMoney( content['quotation']['courseInfo']['fees']['promotion']['pMaterialJpy'])}</td>
                        </tr>
                        <tr style='border-bottom:1px solid #bdbdbd;'>
                            <td nowrap  align='left' valign='top'><b>授業料</b></td><td align='right' valign='top'>{content['quotation']['courseInfo']['weeks']}週間</td><td align='right' valign='top'>￥{__formatMoney( content['quotation']['courseInfo']['fees']['promotion']['pTuitionTotalJpy']) }</td>
                        </tr>
                        <tr>
                            <td height='10'></td>
                        </tr>
                        <tr style='background-color: #F8F9FA;'>
                            <td nowrap align='left' valign='top'><b>滞在オプション料金内容</b></td><td align='right' valign='top'><b>期間／回</b></td><td align='right' valign='top'><b>期間／回</b></td>
                        </tr>"""
    
    if content['quotation']['stay'] == myconst.cst.STAY_OPTION_REQUEST:
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap  align='left' valign='top'><b>滞在手配</b></td><td align='right' valign='top'>1回</td><td align='right' valign='top'>￥{__formatMoney(content['quotation']['schoolInfo']['accommodations'][0]['placementFeeJpy'])}</td></tr>"
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap align='left' valign='top'><b>ホームステイ{content['quotation']['schoolInfo']['accommodations'][0]['roomType']} </b></td><td align='right' valign='top'>{content['quotation']['stayweeks']}週間</td><td align='right' valign='top'>￥{__formatMoney(content['quotation']['schoolInfo']['accommodations'][0]['stayFeeJpy'])}</td></tr>"
        if content['quotation']['pick'] == "True":
            html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap align='left' valign='top'><b>空港送迎（片道）</b></td><td align='right' valign='top'>1回</td><td align='right' valign='top'>￥{__formatMoney(content['quotation']['schoolInfo']['accommodations'][0]['airportPickupFeeJpy'])}</td></tr>"
        else:
            html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap align='left' valign='top'><b>空港送迎（片道）</b></td><td align='right' valign='top'>0回<td align='right' valign='top'>￥0</td></tr>"
    else:
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap  align='left' valign='top'><b>滞在手配</b></td><td align='right' valign='top'>0回</td><td align='right' valign='top'>￥0</td></tr>"
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap align='left' valign='top'><b>ホームステイ{content['quotation']['schoolInfo']['accommodations'][0]['roomType']}</b></td><td align='right' valign='top'>0週間</td><td align='right' valign='top'>　￥0</td></tr>"
        html_body += f"<tr style='border-bottom:1px solid #bdbdbd;'><td nowrap align='left' valign='top'><b>空港送迎（片道）</b></td><td align='right' valign='top'>0回</td><td align='right' valign='top'>￥0</td></tr>"
                        
    html_body += f"""</table>
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>   
                        <tr>
                            <td height='5'></td>
                        </tr> 
                        <tr>
                            <td class='w-space'></td><td class='w-th' align='right' bgcolor='#FEF6F2' valign='top'><b>留学代金 合計**</b></td><td width='w-price' bgcolor='#F8F9FA' align='right' valign='top'><b>￥{__formatMoney(studyAbroadFee)}</b></td>
                        </tr>
                    </table>                       
                <!-- /table -->
                </td>                        
            </tr>
        </table>

        <table width='100%' border='0' align='center' cellpadding='10' cellspacing='0' bgcolor='#fff' class='base'>
            <tr>
                <td>
                    <!-- table -->
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr style='border-bottom: 6px double #222222;'>
                            <td align='left' class='responsive' valign='top'><font color='#222222' style='font-size:16px; font-weight:bold; line-height:1.7; '>見積に含まれていないもの</font></td>
                        </tr>
                  
                        <tr>
                            <td align='left' ><font color='#222222' style='font-size:15px; line-height:1.7; '>"""
                            
    if 'materialNotice' in content['quotation']['schoolInfo']:
        html_body += f"{content['quotation']['schoolInfo']['school']}をお申込みの方へ<br>"
        html_body += f"{content['quotation']['schoolInfo']['materialNotice']}<br><br>"                    
                                
        html_body += f""" 滞在費について<br>
                            滞在オプションとしてご希望いただいたホームステイ期間以降の滞在費は含まれていません。また、ホームステイ開始は原則土日となり、平日開始はできません。平日到着に伴いホテルなどで宿泊される場合の滞在費はお客様のご負担となります。<br>
                            滞在方法や期間、また滞在に伴う費用は留学カウンセラーにご相談ください。<br><br>
                            
                            その他<br>
                            {content['quotation']['countryInfo']['excludedInQuote']}</font></td>
                        </tr>
                    </table>
                </td> 
            </tr> 
        </table>       
            
        <table width='100%' border='0' align='center' cellpadding='10' cellspacing='0' bgcolor='#fff' class='base'>
            <tr>
                <td>
                    <!-- table -->
                    <table border='0' width='100%' cellspacing='0' cellpadding='5' style='font-size:15px;line-height:1.7;'>
                        <tr style='border-bottom: 6px double #222222;'>
                            <td align='left' class='responsive' valign='top'><font color='#222222' style='font-size:16px; font-weight:bold; line-height:1.7; '>その他留意事項</font></td>
                        </tr>
                  
                        <tr>
                            <td align='left' ><font color='#222222' style='font-size:15px; line-height:1.7; '>"""
                               
                                
    if 'homestayNotice' or 'airportPickupNotice' in content['quotation']['schoolInfo']:
        html_body += f"{content['quotation']['schoolInfo']['school']}をお申込みの方へ<br>"
    if 'homestayNotice' in content['quotation']['schoolInfo']:
        html_body += f"・ホームステイ ハイシーズン料金<br>"
        html_body += f"{content['quotation']['schoolInfo']['homestayNotice']}<br><br>"
    if 'airportPickupNotice' in content['quotation']['schoolInfo']:
        html_body += f"・空港送迎について<br>"
        html_body += f"{content['quotation']['schoolInfo']['airportPickupNotice']}<br><br>"                     

    html_body += f"""{content['quotation']['countryInfo']['otherQuoteNotes']}<br><br>

                                **<br>
                                 {__getToday()}時点での当社所定銀行 TTSレートに為替変動リスクヘッジを上乗せして計算いたしております。<br><br>

                                当見積書は18歳以上を対象としています。</font></td>
                        </tr>
                    </table>
                </td> 
            </tr> 
        </table>      

                    
            </td>
          </tr>
        </table><!-- wrap end-->

        <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#F8F9FA'>
            <tr>
                <td>
                    <tr>
                        <td height='20'></td>
                    </tr>
                </td>
            </tr>  
        </table>   
      
        <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#2B2B2B'>
            <tr>
                <td>
                <table width='600' border='0' align='center' cellpadding='0' cellspacing='0' class='base'><!-- wrap-->
                    <tr>
                        <td>

                        <table border='0' width='100%' cellspacing='0' cellpadding='0' style='font-size:15px;line-height:1.7;'>
                            <tbody>
                                <tr>
                                    <td class='responsive' valign='top' align='center'><font color='#ffffff' align='center' style='font-size:15px; line-height:1.7; '>ワールドアベニューの公式SNS</font></td>
                                </tr>
                                <tr>
                                    <td valign='top' align='center' style='padding-top:10px;'><a href='https://works.do/R/ti/p/teigaku@worldavenue'><img src='{images['line.png']}' width='45' alt='' /></a> <a href='https://twitter.com/WorldAvenueJPN'><img src='{images['twitter.png']}' width='45' alt='' /></a> <a href='https://www.facebook.com/worldavenuejapan'><img src='{images['facebook.png']}' width='45' alt='' /></a> <a href='https://www.instagram.com/world_avenue.jpn/'><img src='{images['insta.png']}' width='45' alt='' /></a> <a href='https://www.youtube.com/user/WorldAvenueTokyo'><img src='{images['youtube.png']}' width='45' alt='' /></a></td>
                                </tr>
                            </tbody>
                        <table>
                            
                        <table border='0' width='100%' cellspacing='0' cellpadding='0' style='font-size:15px;line-height:1.7;'>
                            <tbody>
                                <tr>
                                    <td height='20'></td>
                                </tr>
                                <tr>
                                    <td class='responsive' valign='top' align='left'><font color='#ffffff' align='left' style='font-size:15px; line-height:1.7; '>株式会社ワールドアベニュー</font></td>
                                </tr>
                            </tbody>
                        <table>
                        
                        <table border='0' width='100%' cellspacing='0' cellpadding='0' style='font-size:15px;line-height:1.7;'>
                            <tbody>        
                                <tr>
                                    <td class='responsive' valign='top' align='left'><font color='#ffffff' align='left' style='font-size:13px; line-height:1.7; '>J-CORSS認定留学エージェント<br>
                                        住所: 102-0083 東京都千代田区麹町3-5-2BUREX4F<br>
                                        HP: <a style='color:#fff;' href='https://www.world-avenue.co.jp/'>https://www.world-avenue.co.jp/</a></font></td>
                                    <td class='responsive' valign='top' align='left'><font color='#ffffff' align='left' style='font-size:13px; line-height:1.7; '>フリーダイヤル:<a style='color:#fff;' href='tel:0120623385'> 0120-623-385</a><br>
                                        Email:<a style='color:#fff;' href='mailto:japan@world-avenue.co.jp'> japan@world-avenue.co.jp</a><br>
                                        営業時間: 11時～21時｜定休日: 毎週木曜</font></td>    
                                </tr>
                             </tbody>
                        </table> 

                        <table border='0' width='100%' cellspacing='0' cellpadding='0' style='font-size:15px;line-height:1.7;'>
                            <tbody>
                                <tr>
                                    <td height='20'></td>
                                </tr>
                                <tr>
                                    <td class='responsive' valign='top' align='center'><font color='#ffffff' align='center' style='font-size:12px; '>Copyright(c) World Avenue Co.Ltd All Rights Reserved.</font></td>
                                </tr>
                            </tbody>
                        <table>

                    </td>
                </tr>  
            </table><!-- wrap-->

              </td>
            </tr>  
        </table>   
        
            </td>
        </tr>
    </table>
        
          
    </body>
    </html>
                    """

    return html_body
