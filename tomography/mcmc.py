import numpy as np
from scipy.stats import beta, binom
from matplotlib import pyplot as plt 
import copy
from nettopo import topobuild
from tqdm import tqdm
import time

class MetropolisHastings:
    def __init__(self, measures, proposal_dist, accepted_dist, m=1e4, n=1e5):
        """
        Metropolis Hastings
        :param measures: {pair1:[code0Cnt, otherCnt]}
        :param proposal_dist: 建议分布
        :param accepted_dist: 接受分布
        :param m: 收敛步数
        :param n: 迭代步数
        """
        self.measures = measures
        self.proposal_dist = proposal_dist
        self.accepted_dist = accepted_dist
        self.m = m
        self.n = n
        self.netTopo = topobuild.topobuild()
        #netList,net2idx, net2path
        self.netSet = set()
        for pair in self.measures:
            self.netSet = self.netSet.union(self.netTopo.pathnets[pair])
        self.dim = len(self.netSet)
        self.netList = list(self.netSet)
        self.net2idx = {}
        for i, net in enumerate(self.netList):
            self.net2idx[net] = i
        self.net2path = {}
        for pair in self.measures:
            for net in self.netTopo.pathnets[pair]:
                if net not in self.net2path:
                    self.net2path[net] = {pair}
                else:
                    self.net2path[net].add(pair)
    

    @staticmethod
    def __calc_acceptance_ratio(q, p, x, xj_prime, j, measures, netList, net2idx, net2path, pathnets):
        """
        计算接受概率

        :param q: 建议分布
        :param p: 接受分布
        :param x: 上一状态
        :param x_prime: 候选状态
        """
        alpha = p.acceptance(x,j,xj_prime, measures, netList, net2idx, net2path, pathnets)
        #print(alpha)
        return alpha
#         #prob_1 = p.prob(x_prime) * q.joint_prob(x_prime, x)
#         prob_2 = p.prob(x,j, measures, netList, net2idx, net2path, pathnets)
# #         if j == 0:
# #             print(x[j], prob_2)
#         #prob_2 = p.prob(x) * q.joint_prob(x, x_prime)
#         x[j] = xj_prime
#         prob_1 = p.prob(x,j, measures, netList, net2idx, net2path, pathnets)
# #         if j == 0:
# #             print(x[j], prob_1)
#         print(prob_1, prob_2)
#         if prob_2 == 0:
#             alpha = 1.
#         else:
#             alpha = np.min((1., prob_1 / prob_2))
#         return alpha

    def solve(self):
        """
        Metropolis Hastings 算法求解
        """
        all_samples = np.array([np.zeros(self.dim) for _ in range(self.n)])
        # (1) 任意选择一个初始值
        x_0 = np.array([np.random.random() for _ in range(self.dim)])
        for i in tqdm(range(int(self.n))):
            for j in range(self.dim):
                x = x_0 if i == 0 else all_samples[i - 1]
                x[:j] = all_samples[i][:j]
                # (2.a) 从建议分布中抽样选取
                xj_prime = self.proposal_dist.sample()[0]
                # (2.b) 计算接受概率
                xcopy = copy.deepcopy(x)
                alpha = self.__calc_acceptance_ratio(self.proposal_dist, self.accepted_dist, xcopy, xj_prime, j,self.measures, self.netList, self.net2idx, self.net2path, self.netTopo.pathnets)
                #print("alpha: ", alpha)
                # (2.c) 从区间 (0,1) 中按均匀分布随机抽取一个数 u
                u = np.random.uniform(0, 1)
                # 根据 u <= alpha，选择 x 或 x_prime 进行赋值
                if u <= alpha:
                    all_samples[i][j] = xj_prime
                else:
                    all_samples[i][j] = x[j]

        localtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        np.savetxt(localtime+'output.csv', all_samples, delimiter=', ', fmt='%f')
        # (3) 随机样本集合
        samples = all_samples[self.m:]
        # 函数样本均值
        #dist_mean = samples.mean()
        # 函数样本方差
        #dist_var = samples.var()
        #return samples[self.m:], dist_mean, dist_var
        return samples
    
    def topK(self, samples, k=10):
        mean_p = []
        for i in range(len(samples[0])):
            mean_p.append((samples[:, i].mean(),i))
        mean_p.sort(key=lambda x:x[0])
        topk = []
        for i in range(min(k, len(mean_p))):
            topk.append((mean_p[i][0], self.netList[mean_p[i][1]]))
        return topk

    @staticmethod
    def visualize(samples):
        """
        可视化展示
        :param samples: 抽取的随机样本集合
        :param bins: 频率直方图的分组个数
        """
        fig, ax = plt.subplots()
        ax.set_title('Metropolis Hastings')
        mean_p = []
        idxs = []
        for i in range(len(samples[0])):
            mean_p.append(samples[:, i].mean())
            idxs.append(i)
        ax.plot(idxs, mean_p, alpha=0.7, label='Samples Distribution')
        ax.legend()
        plt.show()
        
class ProposalDistribution:
    """
    建议分布
    """

    @staticmethod
    def sample():
        """
        从建议分布中抽取一个样本
        """
        # B(1,1)
        return beta.rvs(1, 1, size=1)

    @staticmethod
    def prob(x):
        """
        P(X = x) 的概率
        """
        return beta.pdf(x, 1, 1)

    def joint_prob(self, x_1, x_2):
        """
        P(X = x_1, Y = x_2) 的联合概率
        """
        return self.prob(x_1) * self.prob(x_2)
class AcceptedDistribution:
    """
    接受分布
    """
    @staticmethod
    def prob(x,j, measures, netList, net2idx, net2path, pathnets): 
        """
        P(X = x) 的概率
        """

        px = 1.0
        net = netList[j]

        for pair in net2path[net]:
            ptmp = 1.0
            for routenet in pathnets[pair]:
                ptmp *= x[net2idx[routenet]]
            px *= ptmp**measures[pair][0]
            px *= (1 - ptmp)**measures[pair][1]

        return px
    
    @staticmethod
    def acceptance(x,j, xj_prime, measures, netList, net2idx, net2path, pathnets): 
        """
        P(X = x) 的概率
        """
        x2 = copy.deepcopy(x)
        x2[j] = xj_prime
        px = 1.0
        net = netList[j]
        alpha = 1.0
        for pair in net2path[net]:
            ptmp = 1.0
            ptmp2 = 1.0
            for routenet in pathnets[pair]:
                ptmp *= x[net2idx[routenet]]
                ptmp2 *= x2[net2idx[routenet]]
            
            alpha *= (xj_prime/x[j])**measures[pair][0]
            alpha *= ((1 - ptmp2)/(1 - ptmp))**measures[pair][1]
        return np.min((1., alpha))