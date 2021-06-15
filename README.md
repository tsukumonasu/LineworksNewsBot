# twitterから定期的に１日分tweetを取得してlineworksに投稿するBot
## 概要
それなりにセキュアにAWS Lambdaで動かす実験をした結果生まれたBotのソースです.  
動かすにはAWS Cloudformation、Lambda、LINEWORKS Botに対してある程度の知識が必要です.  
※このコードは無保証です。一切の損害に対して何の責任も負いません.  

## デプロイ手順
### 事前準備
#### twitter
1. 以下を読んだり公式を翻訳したりして、twitter開発者登録をしてアクセストークンを払い出す.
   - https://qiita.com/newt0/items/66cb76b1c8016e9d0339
#### LINEWORKS
1. https://developers.worksmobile.com/jp/console/openapi/main にアクセスする.
1. 公式サイトの手順を参考に必要なキーを発行する. https://developers.worksmobile.com/jp/document/1002002?lang=ja
    - API ID
    - Service API Consumer Key
    - Server Token (ID 登録タイプ) ※ダウンロードすること
    - 公開設定 は公開
1. https://developers.worksmobile.com/jp/console/bot/form にアクセスしBotを登録する.
    - 必須
        - Bot名
        - 管理者
    - 必要応じてその他も設定する.
    - Botポリシー チーム/グループ/1:Nトークに招待可
1. S3に Server Token をファイル名を `lwlambda.key` に変更してアップロードする.
   - アップロードしたbucketは `LWSERVERKEYBUCKET` としてCFnで使用する。

### layer 作成
1. Pythonを3.8にする.
    ```shell
    python3 -V
    sudo amazon-linux-extras install python3.8 -y
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
    ```
1. pipをインストールする.
    ```shell
    curl -O https://bootstrap.pypa.io/get-pip.py
    python3 get-pip.py
    ```
1. パッケージインストール
    ```shell
    cat <<EOF > requirements.txt
    cryptography
    PyJWT
    requests
    tweepy
    certifi
    chardet
    urllib3
    six
    idna
    cffi
    oauthlib
    pycparser
    EOF
    
    pip install -r requirements.txt -t ./python
    ```
1. s3 アップロード
    ```shell
    zip -r lwtwlambda.zip python
    aws s3 cp lwtwlambda.zip s3://<lwlambda.keyをアップロードしたbucket>/
    ```

### AWS側設定
1. CFnのコンソールから kensho-senkennews-lambda.yaml を使ってスタックを作成する.
2. 作成されたLambdaの以下のキーを暗号化ヘルパーを使用して暗号化する.
   - LW_API_KEY
   - LW_CONSUMER_KEY
   - LW_SERVER_ID
   - TWITTER_ACCESS_TOKEN
   - TWITTER_ACCESS_TOKEN_SECRET
   - TWITTER_CONSUMER_KEY
   - TWITTER_CONSUMER_SECRET
3. 試しに動かしてみて、botからtweetがlineworksに投稿されたら成功です.