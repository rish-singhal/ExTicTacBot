import sys
import random
import signal
import time
import copy
import traceback


class Team6:
    def __init__(self):
        self.hashx = [[[0 for k in range(3)] for j in range(3)]  for i in range(3)]
        self.ply = "x"
        self.conj = "o"
        self.starttime = 0
        self.dict = {}
        self.block_hash = [  [[0 for k in range(3)] for j in range(3)] for i in range(2)]
        self.block_zob = [(2**i)for i in range(18)]
        self.infi = 1000000000
        self.level = 2
        self.ply_blk_won = 0
        self.conj_blk_won = 0
        self.ply_last_blk_won = 0
        self.timer = 24

    def init_zobrist(self, board):
        self.dict = {}
        for k in range(2):
            for i in range(3):
                for j in range(3):
                    self.block_hash[k][i][j] = 0
                    c = 0
                    for m in range(3):
                        for z in range(3):
                            if board.big_boards_status[k][3*i+m][3*j+z] == self.ply:
                                self.block_hash[k][i][j] ^= self.block_zob[2*c]
                            elif board.big_boards_status[k][3*i+m][3*j+z] == self.conj:
                                self.block_hash[k][i][j] ^= self.block_zob[2*c+1]
                            c += 1 

    def update_zubrist_block(self, move, ply):
        if ply == self.ply:
            self.block_hash[move[0]][move[1]/3][move[2] /
                                                3] ^= self.block_zob[(3*(move[1] % 3)+(move[2] % 3)) * 2]
        else:
            self.block_hash[move[0]][move[1]/3][move[2] /
                                                3] ^= self.block_zob[((3*(move[1] % 3)+(move[2] % 3)) * 2)+1]

    def move(self, board, old_move, flag):

        if self.conj == flag:
            self.conj = "x"
            self.ply = "o"

        self.ply_blk_won = 0
        self.conj_blk_won = 0
        if self.ply_last_blk_won:
            self.ply_blk_won = 1

        cells = board.find_valid_move_cells(old_move)
        self.starttime = time.time()-4
        bestval = -self.infi
        selected = cells[random.randrange(len(cells))]
        self.level = 2

        if old_move == (-1, -1, -1):
            return selected

        tt = self.ply_blk_won

        while time.time()-self.starttime < self.timer:

            self.init_zobrist(board)
            d1 = cells[random.randrange(len(cells))]
            bestval = -self.infi
            for c in cells:
                self.update_zubrist_block(c, flag)

                a, b = board.update(old_move, c, flag)
                if b:
                    self.ply_blk_won ^= 1
                else:
                    self.ply_blk_won = 0
                if b and self.ply_blk_won == 1:
                    d = self.minimax(1, 0, -self.infi,
                                     self.infi, c, self.ply, board)
                    self.ply_blk_won = 0
                else:
                    d = self.minimax(1, 0, -self.infi,
                                     self.infi, c, self.conj, board)
                self.update_zubrist_block(c, flag)
                if d > bestval:
                    bestval = d
                    d1 = c

                board.big_boards_status[c[0]][c[1]
                                              ][c[2]] = '-'
                board.small_boards_status[c[0]][c[1] /
                                                3][c[2]/3] = '-'
                if time.time()-self.starttime >= self.timer:
                    break
            if time.time()-self.starttime >= self.timer:
                break
            self.level += 1
            selected = d1
        self.ply_blk_won = tt

        c = selected
        val, won = board.update(old_move, selected, flag)
        board.big_boards_status[selected[0]][selected[1]][selected[2]] = '-'
        board.small_boards_status[c[0]][c[1] /
                                        3][c[2]/3] = '-'
        if won:
            self.ply_last_blk_won ^= 1
        else:
            self.ply_last_blk_won = 0
        return selected

    def new_heuristic(self, ply, move, board):
        boardstate = board.find_terminal_state()
        if boardstate[1] == 'WON':
            if ply == self.ply:
                return self.infi
            else:
                return -self.infi
        for i in range(2):
            for j in range(3):
                for k in range(3):
                    if board.small_boards_status[i][j][k] == self.ply:
                        self.hashx[i][j][k] = 10000000
                    elif board.small_boards_status[i][j][k] == self.conj:
                        self.hashx[i][j][k] = -10000000
                    else:
                        if self.block_hash[i][j][k] in self.dict:
                            self.hashx[i][j][k] = self.dict[self.block_hash[i][j][k]]
                            if len(self.dict) > 1024:
                                self.dict = {}
                        else:
                            self.computecost(board, i, j, k)
                            self.dict[self.block_hash[i][j][k]] = self.hashx[i][j][k]
        return self.computeTotalCost(board)

    def computeTotalCost(self, board):
        ohash = 0
        for k in range(2):
            for i in range(3):
                sumx = 0
                countp = 0
                countq = 0
                for j in range(3):
                    sumx = sumx + self.hashx[k][i][j]
                    if board.small_boards_status[k][i][j] == self.ply:
                        countp += 1
                    if board.small_boards_status[k][i][j] == self.conj:
                        countq += 1

                if countp == 0 or countq == 0:
                    ohash += sumx
            for i in range(3):
                sumx = 0
                countp = 0
                countq = 0
                for j in range(3):
                    sumx = sumx + self.hashx[k][j][i]
                    if board.small_boards_status[k][j][i] == self.ply:
                        countp += 1
                    if board.small_boards_status[k][j][i] == self.conj:
                        countq += 1
                if countp == 0 or countq == 0:
                    ohash += sumx

            sumx = 0
            countp = 0
            countq = 0
            for i in range(3):
                sumx = sumx + self.hashx[k][i][i]
                if board.small_boards_status[k][i][i] == self.ply:
                    countp += 1
                if board.small_boards_status[k][i][i] == self.conj:
                    countq += 1
            if countp == 0 or countq == 0:
                ohash += sumx

            sumx = 0
            countp = 0
            countq = 0
            for i in range(3):
                sumx = sumx + self.hashx[k][2 - i][2 - i]
                if board.small_boards_status[k][2-i][2-i] == self.ply:
                    countp += 1
                if board.small_boards_status[k][2-i][2-i] == self.conj:
                    countq += 1
            if countp == 0 or countq == 0:
                ohash += sumx

        if ohash != 0:
            return ohash

        for i in range(2):
            for j in range(3):
                for k in range(3):
                    ohash += self.hashx[i][j][k]
        return ohash

    def computecost(self, board, i, j, k):
        conj = self.conj
        ply = self.ply
        self.hashx[i][j][k] = 0
        for m in range(3):
            countp = 0
            countj = 0
            for z in range(3):
                if board.big_boards_status[i][j*3+m][k*3+z] == ply:
                    countp = countp + 1
                elif board.big_boards_status[i][j*3+m][k*3+z] == conj:
                    countj = countj + 1
            if countp == 3:
                self.hashx[i][j][k] = self.hashx[i][j][k] + 10000
            elif countp == 2 and countj == 0:
                self.hashx[i][j][k] = self.hashx[i][j][k] + 100
            elif countp == 0 and countj == 2:
                self.hashx[i][j][k] = self.hashx[i][j][k] - 100
            elif countp == 0 and countj == 3:
                self.hashx[i][j][k] = self.hashx[i][j][k] - 10000
            elif countp == 1 and countj == 0:
                self.hashx[i][j][k] = self.hashx[i][j][k] + 1
            elif countp == 0 and countj == 1:
                self.hashx[i][j][k] = self.hashx[i][j][k] - 1

        for m in range(3):
            countp = 0
            countj = 0
            for z in range(3):
                if board.big_boards_status[i][j*3+z][k*3+m] == ply:
                    countp = countp + 1
                elif board.big_boards_status[i][j*3+z][k*3+m] == conj:
                    countj = countj + 1
            if countp == 3:
                self.hashx[i][j][k] = self.hashx[i][j][k] + 10000
            elif countp == 2 and countj == 0:
                self.hashx[i][j][k] = self.hashx[i][j][k] + 100
            elif countp == 0 and countj == 2:
                self.hashx[i][j][k] = self.hashx[i][j][k] - 100
            elif countp == 0 and countj == 3:
                self.hashx[i][j][k] = self.hashx[i][j][k] - 10000
            elif countp == 1 and countj == 0:
                self.hashx[i][j][k] = self.hashx[i][j][k] + 1
            elif countp == 0 and countj == 1:
                self.hashx[i][j][k] = self.hashx[i][j][k] - 1
        countp = 0
        countj = 0
        for m in range(3):
            if board.big_boards_status[i][j*3+m][k*3+m] == ply:
                countp = countp + 1
            elif board.big_boards_status[i][j*3+m][k*3+m] == conj:
                countj = countj + 1
        if countp == 3:
            self.hashx[i][j][k] = self.hashx[i][j][k] + 10000
        elif countp == 2 and countj == 0:
            self.hashx[i][j][k] = self.hashx[i][j][k] + 100
        elif countp == 0 and countj == 2:
            self.hashx[i][j][k] = self.hashx[i][j][k] - 100
        elif countp == 0 and countj == 3:
            self.hashx[i][j][k] = self.hashx[i][j][k] - 10000
        elif countp == 1 and countj == 0:
            self.hashx[i][j][k] = self.hashx[i][j][k] + 1
        elif countp == 0 and countj == 1:
            self.hashx[i][j][k] = self.hashx[i][j][k] - 1
        countp = 0
        countj = 0
        for m in range(3):
            if board.big_boards_status[i][j*3 + 2 - m][k*3 + 2 - m] == ply:
                countp = countp + 1
            elif board.big_boards_status[i][j*3 + 2 - m][k*3 + 2 - m] == conj:
                countj = countj + 1
        if countp == 3:
            self.hashx[i][j][k] = self.hashx[i][j][k] + 10000
        elif countp == 2 and countj == 0:
            self.hashx[i][j][k] = self.hashx[i][j][k] + 100
        elif countp == 0 and countj == 2:
            self.hashx[i][j][k] = self.hashx[i][j][k] - 100
        elif countp == 0 and countj == 3:
            self.hashx[i][j][k] = self.hashx[i][j][k] - 10000
        elif countp == 1 and countj == 0:
            self.hashx[i][j][k] = self.hashx[i][j][k] + 1
        elif countp == 0 and countj == 1:
            self.hashx[i][j][k] = self.hashx[i][j][k] - 1
        return self.hashx[i][j][k]

    def minimax(self, depth, maximise, alpha, beta, old_move, ply, board):
        conj = "o"
        if conj == ply:
            conj = "x"

        if self.ply == ply:
            maximise = 1
        else:
            maximise = 0

        if board.find_terminal_state() != ('CONTINUE', '-') or depth >= self.level or time.time()-self.starttime >= self.timer:
            return self.new_heuristic(conj, old_move, board)

        possible_moves = board.find_valid_move_cells(old_move)

        bestvalue = self.infi
        if ply == self.ply:
            bestvalue = -self.infi

        temp_ply_blk_won = self.ply_blk_won
        temp_conj_blk_won = self.conj_blk_won
        for c in possible_moves:
            val, won = board.update(old_move, c, ply)
            if won:
                if self.ply == ply:
                    self.ply_blk_won ^= 1
                else:
                    self.conj_blk_won ^= 1
            else:
                if self.ply == ply:
                    self.ply_blk_won = 0
                else:
                    self.conj_blk_won = 0

            self.update_zubrist_block(c, ply)
            val = -self.infi

            if self.conj == ply:
                if won and self.conj_blk_won:
                    bestvalue = min(bestvalue, self.minimax(
                        depth+1, 0, alpha, beta, c, ply, board))
                    self.conj_blk_won = 0
                else:
                    bestvalue = min(bestvalue, self.minimax(
                        depth+1, 0, alpha, beta, c, conj, board))
                
                beta = min(bestvalue,beta)
            else:
                if won and self.ply_blk_won:
                    bestvalue = max(bestvalue, self.minimax(
                        depth+1, 0, alpha, beta, c, ply, board))
                    self.ply_blk_won = 0
                else:
                    bestvalue = max(bestvalue, self.minimax(
                        depth+1, 0, alpha, beta, c, conj, board))
                
                alpha = max(alpha,bestvalue)

            board.big_boards_status[c[0]][c[1]
                                          ][c[2]] = '-'
            board.small_boards_status[c[0]][c[1] /
                                            3][c[2]/3] = '-'
            self.update_zubrist_block(c, ply)

            if beta <= alpha or time.time()-self.starttime >= self.timer:
                break
        self.ply_blk_won = temp_ply_blk_won
        self.conj_blk_won = temp_conj_blk_won
        return bestvalue


