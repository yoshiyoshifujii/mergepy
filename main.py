# -*- coding: utf-8 -*-

__version__ = '0.0.2'

from optparse import *
import md5
import os
import shutil

def _hashfile(filepath, hashObject):
    """filepathを開いてhashObjectに格納してハッシュ値を返却する"""
    fileObject = open(filepath, 'rb')
    try:
        while True:
            chunk = fileObject.read(65536)
            if not chunk: break
            hashObject.update(chunk)
    finally:
        fileObject.close()
    return hashObject.hexdigest()

def md5file(filepath):
    """filepathのmd5ハッシュを取得して返却する"""
    hashObject = md5.new()
    return _hashfile(filepath, hashObject)

def walk_path_and_create_map(path, opts):
    path = "%s%s" % (os.path.abspath(path), os.path.sep)
    result_map = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for d in (os.path.join(dirpath, dirname) for dirname in dirnames):
            if d in result_map: raise
            if opts.exclude and opts.exclude in d: continue
            result_map[d.replace(path, "")] = "dir"
        for f in (os.path.join(dirpath, filename) for filename in filenames):
            if f in result_map: raise
            if opts.exclude and opts.exclude in f: continue
            result_map[f.replace(path, "")] = md5file(f)
    return result_map

def copy(target, output):
    if os.path.isfile(target):
        output_dir = os.path.split(output)[0]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        shutil.copy2(target, output)
    else:
        shutil.copytree(target, output)

def main(source_path, target_path, output_path, opts=None):
    """
    比較元のフォルダと比較先のフォルダを再帰的に走査しハッシュ比較した結果、
    比較先のフォルダに追加、変更、削除された一覧とファイルを構造を保ったまま出力する。
    """

    # 出力先のパスが存在するなら削除
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path)

    source_map = walk_path_and_create_map(source_path, opts)
    target_map = walk_path_and_create_map(target_path, opts)

    # 削除になったパスを抽出
    delete_path_list = sorted(list(set(source_map.keys()) - set(target_map.keys())))

    # 追加になったパスを抽出
    add_path_list = sorted(list(set(target_map.keys()) - set(source_map.keys())))

    # 変更になったパスを抽出
    edit_path_list = []
    for s_key, s_value in source_map.items():
        # 比較元と同じパスの比較先のハッシュ値を取得
        t_value = target_map.get(s_key, None)

        # 取得できなかったら削除か追加なので無視
        if t_value is None: continue

        # 比較元と比較先のハッシュ値が異なる場合はパスを追加
        if s_value != t_value:
            edit_path_list.append(s_key)
    edit_path_list = sorted(edit_path_list)

    w = open(os.path.join(output_path, "__result.txt"), "wb")

    try:
        #削除のパスを出力
        if delete_path_list:
            w.write("#削除\n")
            [w.write("%s\n" % delete_path_value) for delete_path_value in delete_path_list]

        #追加のパスを出力
        if add_path_list:
            w.write("#追加\n")
            for add_path_value in add_path_list:
                w.write("%s\n" % add_path_value)
                if opts.isexport:
                    copy(os.path.join(target_path, add_path_value), os.path.join(output_path, add_path_value))

        #変更のパスを出力
        if edit_path_list:
            w.write("#変更\n")
            for edit_path_value in edit_path_list:
                w.write("%s\n" % edit_path_value)
                if opts.isexport:
                    copy(os.path.join(target_path, edit_path_value), os.path.join(output_path, edit_path_value))
    finally:
        w.close()

def validate_args(args):
    """固定引数の指定が正しいか確認する
    """

    # 引数が空はダメ
    if not args:
        return False

    # 引数のサイズは3以外ダメ
    if not len(args) == 3:
        return False

    def _validate_args(source_path, target_path, output_path):

        #source_pathが空だとダメ
        if not source_path:
            return False

        # source_pathが存在しないのはダメ
        if  not os.path.exists(source_path):
            return False

        #target_pathが空だとダメ
        if not target_path:
            return False

        # target_pathが存在しないのはダメ
        if  not os.path.exists(target_path):
            return False

        #output_pathが空だとダメ
        if not output_path:
            return False

        # output_pathが存在しないのはダメ→仕様変更でOK。あとで無いなら作成する。
        #if  not os.path.exists(output_path):
        #   return False

        # 上記全てOK
        return True

    # 引数のどれかがダメ
    if not _validate_args(*args):
        return False

    # 上記全てOK
    return True

if __name__ == "__main__":
    option_parser = OptionParser(version="ver:%s" % __version__)

    # 使い方の説明
    option_parser.set_usage(u"%s 参照元のパス 参照先のパス 出力先のパス" % option_parser.get_usage()[:-1])

    option_parser.add_option("-X", "--exclude", action="store", dest="exclude", help=u"除外する条件を指定できます")

    option_parser.add_option("-o", action="store_true", dest="isexport", help=u"差分をエクスポートします")
    option_parser.add_option("-n", action="store_false", dest="isexport", help=u"差分をエクスポートしません", default=False)

    opts, args = option_parser.parse_args()

    if validate_args(args):
        main(opts=opts, *args)
    else:
        option_parser.print_help()

