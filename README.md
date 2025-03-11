# QV ペンで描いた絵を Blender に読み込むやつ / Import QV-Pen Line Data to Blender

## 概要

### 日本語

このプラグインは QV-Pen のデータを Blender にインポートするためのものです。

QV ペンのデータを Dolphiiiin 様作成の「QvPen Exporter / Importer」（https://booth.pm/ja/items/6499949）が設置されたワールドでエクスポートし、「QvPen Export Formatter」（https://dolphiiiin.github.io/qvpen-export-formatter/）を使ってJSONファイルに変換したものを本ツールに読み込ませるとメッシュ化したパスとしてインポートできます。

色と太さが引き継がれます。

座標は、VRC のワールド上で描かれた場所と対応します。

### English

This plugin imports QV-Pen line data to Blender. Export QV-Pen data from the world where Dolphiiiin's "QvPen Exporter / Importer" (https://booth.pm/ja/items/6499949) is installed, and use "QvPen Export Formatter" (https://dolphiiiin.github.io/qvpen-export-formatter/) to convert it into a JSON file. This tool can import the converted JSON file as a mesh path. The color and thickness are inherited. The coordinates correspond to the location where the line is drawn on the VRC world.

## 使い方

### 日本語

- インストールすると N パネルに「QV Pen」という名のパネルができるので、そこを開いてください。
- パネルの中には「Select JSON File」というボタンがあるので、それを押して前述のツールで作成した JSON ファイルを選択してください。
- 基本的にはワールドに設置されている QV Pen の太さ情報を読み込みます。太さが未定義の場合はこの入力欄に設定した太さが適用されます。
- 「Add Solidify Modifier」にチェックを入れると、太さに応じてソリッド化モディファイアが追加されます。メッシュ化したい場合はこれを有効にしてください。
- 「Generate Paths」を押すと、パスもしくはソリッド化したメッシュが生成されます。
- 生成されたパスは「QVPen_Paths_Parent」という親オブジェクトの下にまとめられます。
- シェーダータイプを「Principled BSDF」と「放射シェーダー」から選択できます。
  - Principled BSDF はメッシュの形状が目立ち、陰影がはっきり出ます。
  - 放射シェーダーはどの角度からも均一に見え、QVPen の見え方に近いですが、発光するため色合いが異なります。
  - 放射シェーダーを選択した場合、放射強度を調整できます。

### English

- After installing, a panel named "QV Pen" will be created in the N panel. Open it.
- There is a button called "Select JSON File" in the panel. Click it to select the JSON file created by the above tool.
  - The default extrude value can be changed to override it uniformly.
- If "Add Solidify Modifier" is checked, a solidify modifier will be added according to the thickness. If you want to mesh, please enable it.
- Click "Generate Paths" to generate a path or a solidified mesh.
- The generated paths will be grouped under a parent object named "QVPen_Paths_Parent".
- You can select between "Principled BSDF" and "Emission" shader types.
  - Principled BSDF highlights the shape of the mesh and shows clear shadows.
  - Emission shader type looks uniform from any angle, similar to QVPen's appearance, but with different color tones due to light emission.
  - If you select the Emission shader type, you can adjust the emission intensity.

## 注意点

### 日本語

- 座標は VRC のワールド上で描かれた場所と対応します。
- QVPen のデータの完全再現を保証するものではありません。
- 小数の問題で座標に多少のずれが生じる場合があります。

### English

- The coordinates correspond to the location where the line is drawn on the VRC world.
- QVPen's data is not guaranteed to be fully reproduced.
- There may be some deviation in the coordinates due to the decimal problem.
